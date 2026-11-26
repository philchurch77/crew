"""Chat rules that span more than one model or request."""
import logging

from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from . import tools
from .models import ChatTurn, ModelCall, ToolCall
from .prompts import PROMPT_VERSION, system_prompt
from .streaming import AgentConfig, NUL

logger = logging.getLogger(__name__)

# Bounds the payload and the bill; every turn stays stored.
API_HISTORY_TURNS = 20

# Each message is a paid call. Counted in the shared cache.
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60

SOURCES_NOT_SAVED_NOTE = "\n\n[the sources for this reply could not be saved]"


def build_agent(user):
    """The assistant for this user. Anything per-user belongs in the tools'
    handlers, not in the prompt (which must stay byte-stable)."""
    return AgentConfig(
        system=system_prompt(settings.ASSISTANT_NAME),
        model=settings.AI_MODEL,
        effort=settings.AI_EFFORT,
        tools=tuple(tools.definitions()),
        tool_labels=tools.labels(),
    )


def api_history(session, message):
    """The conversation sent to the model: the text of THIS session's last
    turns, opening on a user turn, then the new message. Nothing from
    another chat or another person; tool results reach the model only
    inside the loop that produced them."""
    recent = list(session.turns.order_by("-timestamp", "-pk").values("role", "content")[:API_HISTORY_TURNS])
    history = recent[::-1]
    while history and history[0]["role"] != ChatTurn.ROLE_USER:
        history.pop(0)
    history.append({"role": ChatTurn.ROLE_USER, "content": message})
    return history


def rate_limited(user):
    """True once this user has spent the window. Not cache.incr():
    FileBasedCache's incr() resets the timeout."""
    key = f"chat-rate:{user.pk}"
    if cache.add(key, 1, RATE_LIMIT_WINDOW_SECONDS):
        return False
    count = cache.get(key)
    if count is None:  # expired between add() and get()
        cache.add(key, 1, RATE_LIMIT_WINDOW_SECONDS)
        return False
    if count >= RATE_LIMIT_REQUESTS:
        return True
    cache.set(key, count + 1, RATE_LIMIT_WINDOW_SECONDS)
    return False


def without_nul(value):
    """NULs out, through lists and dicts: jsonb refuses them."""
    if isinstance(value, str):
        return value.replace(NUL, "")
    if isinstance(value, dict):
        return {without_nul(k): without_nul(v) for k, v in value.items()}
    if isinstance(value, list):
        return [without_nul(v) for v in value]
    return value


def record_run(session, user, agent, run):
    """Log the call, and save the reply with its look-ups in one
    transaction. The log is written whatever happened, reply or none."""
    ModelCall.objects.create(
        user=user, session=session, model=agent.model, prompt_version=PROMPT_VERSION,
        api_calls=run.api_calls, tool_calls=len(run.tool_calls),
        input_tokens=run.input_tokens, output_tokens=run.output_tokens,
        cache_read_tokens=run.cache_read_tokens, latency_ms=run.latency_ms,
        outcome=run.outcome,
    )
    if not run.text:
        return None
    try:
        with transaction.atomic():
            turn = ChatTurn.objects.create(session=session, role=ChatTurn.ROLE_ASSISTANT, content=run.text)
            ToolCall.objects.bulk_create(
                ToolCall(
                    turn=turn, sequence=call.sequence, tool_name=call.name,
                    input=without_nul(call.input), result=without_nul(call.result),
                    source=without_nul(call.source), is_error=call.is_error,
                )
                for call in run.tool_calls
            )
            session.save(update_fields=["updated_at"])
        return turn
    except Exception:
        if not run.tool_calls:
            raise
        # Losing what was read is worse than losing its record.
        logger.exception("Failed to save the look-ups; saving the reply alone")
        with transaction.atomic():
            turn = ChatTurn.objects.create(
                session=session, role=ChatTurn.ROLE_ASSISTANT, content=run.text + SOURCES_NOT_SAVED_NOTE
            )
            session.save(update_fields=["updated_at"])
        return turn


def sources(session):
    """The labels of what was looked up in this chat, each once, in order.
    Labels only: never an input or a result."""
    seen = ToolCall.objects.filter(turn__session=session, is_error=False).exclude(source="")
    return list(dict.fromkeys(seen.order_by("turn__timestamp", "sequence").values_list("source", flat=True)))
