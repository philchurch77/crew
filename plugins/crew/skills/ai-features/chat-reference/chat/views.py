import json
import logging
import re
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST, require_safe

from . import services
from .models import ChatSession, ChatTurn
from .streaming import NUL, stream_reply
from .tools import runner_for

logger = logging.getLogger(__name__)

SESSION_KEY = "chat_session_key"
HISTORY_LIMIT = 20  # the sidebar; not the API's window
SIDEBAR_CHARS = 50
HEADER_CHARS = 120

# fullmatch, not $: "$" lets a trailing "\n" through.
SESSION_KEY_CHARS = re.compile(r"[A-Za-z0-9_-]+")


def _usable_key(key):
    """A key that could be stored. Refused before any query, so a bad key
    is a 404 and never a database error."""
    max_length = ChatSession._meta.get_field("session_key").max_length
    return (isinstance(key, str) and len(key) <= max_length
            and SESSION_KEY_CHARS.fullmatch(key) is not None)


def _get_owned_session(user, session_key):
    """The user's own chat by key, or 404: unknown, unowned and unusable
    keys alike, so the answer never says whether a chat exists."""
    if not _usable_key(session_key):
        raise Http404
    return get_object_or_404(ChatSession.objects.for_user(user), session_key=session_key)


def _json_login_required(view):
    """401 JSON when signed out: a login redirect reaches fetch() as a 200
    page (article 8)."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"error": "You have been signed out. Sign in again, then try once more."}, status=401
            )
        return view(request, *args, **kwargs)
    return wrapped


def _history(user, current_key):
    sessions = list(ChatSession.objects.for_user(user)[:HISTORY_LIMIT])
    return [
        {"key": s.session_key, "label": s.label(SIDEBAR_CHARS), "current": s.session_key == current_key}
        for s in sessions
    ]


@login_required
def chat_page(request):
    if request.GET.get("new") == "1":
        request.session[SESSION_KEY] = get_random_string(32)
        return redirect("chat")

    requested = request.GET.get("session_id")
    if requested:
        # Only an owned key, so a guessed one never becomes this browser's.
        session = _get_owned_session(request.user, requested)
        request.session[SESSION_KEY] = session.session_key
    else:
        if not request.session.get(SESSION_KEY):
            request.session[SESSION_KEY] = get_random_string(32)
        session = ChatSession.objects.for_user(request.user).filter(
            session_key=request.session[SESSION_KEY]
        ).first()

    key = session.session_key if session else request.session[SESSION_KEY]
    return render(request, "chat/chat.html", {
        "session_key": key,
        # The h1, never <title>: browser history keeps titles.
        "chat_title": session.label(HEADER_CHARS) if session else "",
        "chat_turns": [{"role": t.role, "content": t.content} for t in session.turns.all()] if session else [],
        "chat_history": _history(request.user, key),
        "chat_sources": services.sources(session) if session else [],
    })


@require_POST
def stream_chat(request):
    # 401, not a login redirect, so the page keeps the text to resend.
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "You have been signed out. Your message is still in the box: "
                      "sign in in another tab, then send it again."},
            status=401,
        )
    if services.rate_limited(request.user):
        return JsonResponse(
            {"error": "You're sending messages a little too quickly. Wait a minute and try again."},
            status=429,
        )
    try:
        data = json.loads(request.body)
        # Before anything uses it, so what is sent is what is stored.
        message = str(data.get("message", "")).replace(NUL, "").strip()
        if not message:
            return JsonResponse({"error": "Message is empty."}, status=400)

        # The page, not the cookie (shared by tabs), names the chat. A new
        # key makes a new chat; another person's key is a 404.
        key = data.get("session_key")
        if not _usable_key(key):
            raise Http404
        if ChatSession.objects.filter(session_key=key).exclude(user=request.user).exists():
            raise Http404
        session, _ = ChatSession.objects.get_or_create(user=request.user, session_key=key)

        history = services.api_history(session, message)
        # Built before the turn is saved: the page reads any answer that is
        # not a stream as "nothing was saved".
        agent = services.build_agent(request.user)
        run_tool = runner_for(request.user)

        # Saved before the stream opens, so it survives a failed one.
        with transaction.atomic():
            ChatTurn.objects.create(session=session, role=ChatTurn.ROLE_USER, content=message)
            session.save(update_fields=["updated_at"])

        user = request.user
        return StreamingHttpResponse(
            stream_reply(agent, history, run_tool,
                         on_complete=lambda run: services.record_run(session, user, agent, run)),
            content_type="text/plain; charset=utf-8",
        )
    except Http404:
        raise
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception:
        # The exception only: never the message, never echoed.
        logger.exception("Chat stream setup failed")
        return JsonResponse({"error": "Something went wrong. Please try again."}, status=500)


@_json_login_required
@require_safe
def chat_history(request):
    """After a reply or a rename: the sidebar, and this chat's title and
    sources. A key that is not this user's chat (a new chat not yet saved,
    or anyone else's) gets the sidebar alone, and says nothing else."""
    key = request.GET.get("session_id")
    session = (
        ChatSession.objects.for_user(request.user).filter(session_key=key).first()
        if _usable_key(key) else None
    )
    return JsonResponse({
        "history": render_to_string(
            "chat/partials/history.html",
            {"chat_history": _history(request.user, session.session_key if session else None)},
            request=request,
        ),
        "sources": render_to_string(
            "chat/partials/sources.html",
            {"chat_sources": services.sources(session) if session else []}, request=request,
        ),
        "title": session.label(HEADER_CHARS) if session else "",
    })


@_json_login_required
@require_POST
def rename_chat(request, session_key):
    session = _get_owned_session(request.user, session_key)
    try:
        title = str(json.loads(request.body).get("title", "")).replace(NUL, "").strip()
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    if not title:
        return JsonResponse({"error": "A title cannot be empty."}, status=400)
    # Not updated_at: a rename should not move a chat up the sidebar.
    session.title = title
    session.save(update_fields=["title"])
    return JsonResponse({"status": "ok"})


@login_required
@require_POST
def delete_chat(request, session_key):
    _get_owned_session(request.user, session_key).delete()
    if request.session.get(SESSION_KEY) == session_key:
        request.session[SESSION_KEY] = None
    return redirect("chat")


@login_required
@require_safe
def export_chat(request, session_key):
    """The chat exactly as stored, as plain text."""
    session = _get_owned_session(request.user, session_key)
    lines = [f"{turn.role.upper()}: {turn.content}" for turn in session.turns.all()]
    response = HttpResponse("\n\n".join(lines), content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="chat_{session.pk}.txt"'
    return response
