"""Two JSON endpoints: ask for a suggestion, accept an edited one. A signed-
out caller gets 401 JSON (article 1). The model never writes the record;
the accept view saves the teacher's text as theirs (article 13).

Adapt pupils_for() and targets_for() to the project's school link."""
from functools import wraps

from django.apps import apps
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Suggestion
from .services import ask

SERVICE_OUTCOMES = {"timeout", "rate_limited", "error", "cap", "no_corpus"}


def json_login_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"ok": False, "error": "signed_out"}, status=401)
        return view(request, *args, **kwargs)

    return wrapped


def pupils_for(user):
    """Every pupil this user may ask about. Filtered by school (article 1)."""
    Pupil = apps.get_model(settings.AI_PUPIL_MODEL)
    return Pupil.objects.filter(school__memberships__user=user)


def targets_for(user):
    """Every record this user may write an accepted suggestion onto."""
    Target = apps.get_model(settings.AI_TARGET_MODEL)
    return Target.objects.filter(pupil__school__memberships__user=user)


def pupil_names(pupil):
    return [getattr(pupil, f, "") for f in getattr(settings, "AI_PUPIL_NAME_FIELDS", ("first_name", "last_name"))]


@json_login_required
@require_POST
def suggest(request):
    pupil = get_object_or_404(pupils_for(request.user), pk=request.POST.get("pupil"))
    question = (request.POST.get("question") or "").strip()
    if not question or len(question) > 2000:
        return JsonResponse({"ok": False, "error": "bad_question"}, status=400)
    result = ask(
        user=request.user,
        school_id=pupil.school_id,
        pupil_ref=f"pupil:{pupil.pk}",
        names=pupil_names(pupil),
        question=question,
    )
    if not result.ok:
        status = 503 if result.call.outcome in SERVICE_OUTCOMES else 200
        return JsonResponse({"ok": False, "error": result.call.outcome, "message": result.message}, status=status)
    s = result.suggestion
    return JsonResponse(
        {"ok": True, "suggestion": s.pk, "answer": s.answer, "grounded": s.grounded, "citations": s.citations}
    )


@json_login_required
@require_POST
def accept(request, pk):
    suggestion = get_object_or_404(Suggestion, pk=pk, user=request.user)
    text = (request.POST.get("text") or "").strip()
    if not text:
        return JsonResponse({"ok": False, "error": "empty"}, status=400)
    target = get_object_or_404(targets_for(request.user), pk=request.POST.get("target"))
    setattr(target, settings.AI_TARGET_FIELD, text)
    target.model_assisted = True
    target.full_clean()
    target.save()
    suggestion.accepted_at = timezone.now()
    suggestion.accepted_text = text
    suggestion.save(update_fields=["accepted_at", "accepted_text"])
    return JsonResponse({"ok": True})
