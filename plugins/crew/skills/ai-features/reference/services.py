"""The one place the model is called. Retrieval, redaction, the payload as
data, one call with a timeout, every outcome logged, nothing written to a
record (article 13)."""
import logging
import re
import time
from dataclasses import dataclass

import anthropic
from django.conf import settings
from django.db import connection
from django.db.models import F, Q, Sum
from django.utils import timezone

from .models import Corpus, ModelCall, Passage, Suggestion
from .prompts import PROMPT_VERSION, system_prompt, user_prompt
from .redact import redact

log = logging.getLogger(__name__)
CITATION = re.compile(r"\[P(\d+)\]")
MESSAGES = {
    "refused": "The assistant declined to answer this question.",
    "timeout": "The assistant took too long. Your text is unchanged; try again.",
    "rate_limited": "The assistant is busy. Your text is unchanged; try again in a minute.",
    "error": "The assistant is unavailable. Your text is unchanged.",
    "cap": "This school has used its assistant allowance for the month.",
    "no_corpus": "No guidance has been loaded for the assistant yet.",
}

_client = None


def client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(timeout=30.0, max_retries=1)
    return _client


@dataclass
class Result:
    call: ModelCall
    suggestion: Suggestion | None = None

    @property
    def ok(self):
        return self.suggestion is not None

    @property
    def message(self):
        return MESSAGES.get(self.call.outcome, "")


def current_corpus():
    return Corpus.objects.filter(is_current=True).first()


def retrieve(question, corpus, limit=6):
    """Passages most likely to answer the question. Postgres full-text search
    in production; a word-overlap fallback on SQLite in development."""
    qs = Passage.objects.filter(document__corpus=corpus).select_related("document")
    if connection.vendor == "postgresql":
        from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

        query = SearchQuery(question, search_type="websearch")
        return list(
            qs.annotate(rank=SearchRank(SearchVector("text", "section"), query))
            .filter(rank__gt=0)
            .order_by("-rank")[:limit]
        )
    words = {w for w in re.findall(r"[a-z]{4,}", question.lower())}
    if not words:
        return []
    filters = Q()
    for w in words:
        filters |= Q(text__icontains=w) | Q(section__icontains=w)
    candidates = list(qs.filter(filters)[:100])
    candidates.sort(key=lambda p: -sum(w in (p.text + p.section).lower() for w in words))
    return candidates[:limit]


def cap_reached(school_id):
    cap = settings.AI_MONTHLY_TOKEN_CAP
    if cap <= 0:
        return True
    start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    used = ModelCall.objects.filter(school_id=school_id, created_at__gte=start).aggregate(
        n=Sum(F("input_tokens") + F("output_tokens"))
    )["n"] or 0
    return used >= cap


def build_payload(question, passages, names=()):
    """Exactly what will be sent, as data, so a test or the Master-at-Arms
    can read it before it goes anywhere. Returns (payload, redacted question)."""
    redacted, _ = redact(question, names)
    payload = {
        "model": settings.AI_MODEL,
        "max_tokens": 1024,
        "system": system_prompt(),
        "messages": [{"role": "user", "content": user_prompt(redacted, passages)}],
        "output_config": {"effort": settings.AI_EFFORT},
    }
    return payload, redacted


def ask(*, user, school_id, pupil_ref, names, question):
    corpus = current_corpus()
    call = ModelCall(
        user=user,
        school_id=school_id,
        pupil_ref=pupil_ref,
        model=settings.AI_MODEL,
        prompt_version=PROMPT_VERSION,
        corpus_version=corpus.version if corpus else "",
    )
    if corpus is None:
        return _finish(call, "no_corpus")
    if cap_reached(school_id):
        return _finish(call, "cap")

    passages = retrieve(question, corpus)
    payload, redacted = build_payload(question, passages, names)
    if settings.AI_KEEP_REQUEST_TEXT:
        call.request_text = payload["messages"][0]["content"]

    started = time.monotonic()
    try:
        if getattr(settings, "AI_FALLBACKS", True):
            response = client().beta.messages.create(
                **payload, betas=["server-side-fallback-2026-07-01"], fallbacks="default"
            )
        else:
            response = client().messages.create(**payload)
    except anthropic.APITimeoutError:
        return _finish(call, "timeout", started)
    except anthropic.RateLimitError:
        return _finish(call, "rate_limited", started)
    except anthropic.APIStatusError as e:
        log.warning("assistant: API error %s %s", e.status_code, getattr(e, "message", ""))
        return _finish(call, "error", started)
    except anthropic.APIConnectionError:
        return _finish(call, "error", started)

    call.request_id = getattr(response, "_request_id", "") or ""
    call.input_tokens = response.usage.input_tokens
    call.output_tokens = response.usage.output_tokens
    if response.stop_reason == "refusal":
        return _finish(call, "refused", started)

    text = "".join(b.text for b in response.content if b.type == "text").strip()
    sent = {p.id: p for p in passages}
    cited = [int(i) for i in dict.fromkeys(CITATION.findall(text)) if int(i) in sent]
    call.grounded = bool(cited)
    _finish(call, "ok", started)
    suggestion = Suggestion.objects.create(
        call=call,
        user=user,
        school_id=school_id,
        pupil_ref=pupil_ref,
        question=redacted,
        answer=text,
        grounded=call.grounded,
        citations=[{"passage_id": i, "ref": sent[i].ref()} for i in cited],
    )
    return Result(call, suggestion)


def _finish(call, outcome, started=None):
    call.outcome = outcome
    if started is not None:
        call.latency_ms = int((time.monotonic() - started) * 1000)
    call.save()
    return Result(call)
