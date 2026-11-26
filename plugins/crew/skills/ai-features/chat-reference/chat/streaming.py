"""The model call and its tool loop, as a generator for
StreamingHttpResponse. The one place the model is called.

Do not tidy:
- Exceptions are caught INSIDE the generator: it runs after the view has
  returned, so nothing outside can catch them. Never make the response
  synchronous.
- The loop's history is append-only, and assistant content goes back
  verbatim, thinking blocks included.
- MAX_API_CALLS is the cost control on one message.
"""
import json
import logging
import time
from dataclasses import dataclass, field

import anthropic

logger = logging.getLogger(__name__)

# Generic on purpose: never the exception's own words.
STREAM_ERROR_MESSAGE = (
    "\n\nSorry, something went wrong while writing this reply. "
    "Please send your message again."
)
REFUSAL_MESSAGE = "I can't help with that one. Try asking it another way."
CUT_SHORT_MESSAGE = "[reply cut short]"
TOO_MANY_LOOKUPS_MESSAGE = (
    "[I stopped before finishing: this needed more look-ups than one reply "
    "allows. Try a narrower question.]"
)
EMPTY_REPLY_MESSAGE = "No reply came back this time. Please send your message again."
INCOMPLETE_MARKER = "\n\n[reply incomplete: the connection failed]"
# To the model, in place of a tool result, once the budget is spent.
TOOL_LIMIT_RESULT = (
    "Tool limit reached for this message. Answer now from what you already "
    "have, and say what you could not check."
)

# Thinking spends from this too, so well above any reply.
MAX_TOKENS = 16000
MAX_API_CALLS = 6
# Rounds whose tools run; the next gets TOOL_LIMIT_RESULT, so the last
# call is spent answering.
TOOL_ROUNDS = MAX_API_CALLS - 2

# A status frame (\x1e label \x1e) tells the page what is happening. It is
# never part of the reply: the separator is stripped from model text, so a
# frame can only come from here.
STATUS_SEP = "\x1e"
DEFAULT_STATUS = "Working…"
NUL = "\x00"  # Postgres refuses one in text


def status(label):
    return f"{STATUS_SEP}{label}{STATUS_SEP}"


def _clean(chunk):
    return chunk.replace(STATUS_SEP, "").replace(NUL, "")


_client = None


def _get_client():
    """Built on first use, so management commands run without a key. The
    SDK reads ANTHROPIC_API_KEY; never log at debug on a deployment
    (ANTHROPIC_LOG), which would print what people typed."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


@dataclass(frozen=True)
class AgentConfig:
    system: str
    model: str
    # Explicit, so a model change cannot change it.
    effort: str = "medium"
    max_tokens: int = MAX_TOKENS
    tools: tuple = ()
    # Tool name -> the status line shown while it runs.
    tool_labels: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ToolCallRecord:
    sequence: int
    name: str
    input: dict
    result: dict
    source: str
    is_error: bool


@dataclass
class AgentRun:
    """What on_complete receives, once, however the run ended."""

    text: str = ""
    tool_calls: list = field(default_factory=list)
    outcome: str = "ok"
    api_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    latency_ms: int = 0

    @property
    def incomplete(self):
        return self.outcome in ("error", "disconnected")


def request_kwargs(agent, convo):
    """Exactly what is sent, as data, so a test or a reviewer can read it.
    Never add temperature, top_p, top_k, budget_tokens, a prefilled
    assistant turn or a forced tool_choice: this model answers 400."""
    kwargs = {
        "model": agent.model,
        "max_tokens": agent.max_tokens,
        "system": agent.system,
        "messages": convo,
        "output_config": {"effort": agent.effort},
        # Caches tools + system prompt + the history prefix between calls.
        "cache_control": {"type": "ephemeral"},
    }
    if agent.tools:
        kwargs["tools"] = list(agent.tools)
    return kwargs


def stream_reply(agent, messages, run_tool, on_complete):
    """Yield text deltas and status frames for one reply.

    ``run_tool(name, input) -> (result, source, is_error)`` must not raise.
    ``on_complete(run)`` is called exactly once, however the run ends, and
    may raise: it is wrapped, because the response is already going out.
    """
    run = AgentRun()
    convo = list(messages)
    started = time.monotonic()

    def finish(outcome=None):
        if outcome:
            run.outcome = outcome
        run.latency_ms = int((time.monotonic() - started) * 1000)
        if run.incomplete and run.text:
            run.text += INCOMPLETE_MARKER
        try:
            on_complete(run)
        except Exception:
            logger.exception("Failed to save the reply")

    try:
        client = _get_client()
        stop_reason = None
        for call_no in range(1, MAX_API_CALLS + 1):
            yield status("Thinking…")
            round_started = False
            with client.messages.stream(**request_kwargs(agent, convo)) as stream:
                for chunk in stream.text_stream:
                    chunk = _clean(chunk)
                    if not chunk:
                        continue
                    if not round_started and run.text and not run.text.endswith("\n"):
                        # Text after a tool round starts a new paragraph.
                        chunk = "\n\n" + chunk
                    round_started = True
                    run.text += chunk
                    yield chunk
                final = stream.get_final_message()

            run.api_calls = call_no
            run.input_tokens += final.usage.input_tokens or 0
            run.output_tokens += final.usage.output_tokens or 0
            run.cache_read_tokens += getattr(final.usage, "cache_read_input_tokens", 0) or 0

            stop_reason = final.stop_reason
            tool_uses = [b for b in final.content if b.type == "tool_use"]
            if stop_reason != "tool_use" or not tool_uses or call_no == MAX_API_CALLS:
                break

            convo.append({"role": "assistant", "content": final.content})
            results = []
            for block in tool_uses:
                if call_no <= TOOL_ROUNDS:
                    yield status(agent.tool_labels.get(block.name, DEFAULT_STATUS))
                    result, source, is_error = run_tool(block.name, block.input)
                else:
                    # The next call is the last: answer, don't ask for more.
                    result, source, is_error = {"error": TOOL_LIMIT_RESULT}, "", True
                run.tool_calls.append(ToolCallRecord(
                    sequence=len(run.tool_calls) + 1, name=block.name, input=block.input,
                    result=result, source=source, is_error=is_error,
                ))
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, ensure_ascii=False),
                    "is_error": is_error,
                })
            # Every result for the round in ONE user message.
            convo.append({"role": "user", "content": results})

        if stop_reason == "refusal":
            run.outcome, ending = "refused", REFUSAL_MESSAGE
        elif stop_reason == "max_tokens":
            run.outcome, ending = "cut_short", CUT_SHORT_MESSAGE
        elif stop_reason == "tool_use":  # still asking after the last call
            run.outcome, ending = "tool_limit", TOO_MANY_LOOKUPS_MESSAGE
        elif not run.text:
            run.outcome, ending = "empty", EMPTY_REPLY_MESSAGE
        else:
            ending = ""
        if ending:
            if run.text:
                ending = "\n\n" + ending
            run.text += ending
            yield ending
    except GeneratorExit:
        # The browser went away. Not an Exception: save what was read,
        # then close; nothing may be yielded.
        finish("disconnected")
        raise
    except Exception:
        # The exception, never the conversation.
        logger.exception("The model call failed")
        yield STREAM_ERROR_MESSAGE
        finish("error")
        return

    finish()
