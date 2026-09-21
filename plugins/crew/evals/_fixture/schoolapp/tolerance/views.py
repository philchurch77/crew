from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from schools.models import Pupil

from .forms import ObservationForm
from .models import Observation


def _school_for(user):
    return user.membership.school


@login_required
def observation_list(request):
    school = _school_for(request.user)
    pupils = Pupil.objects.filter(school=school)
    observations = Observation.objects.filter(pupil__school=school)
    pupil_id = request.GET.get("pupil")
    if pupil_id:
        observations = Observation.objects.filter(pupil_id=pupil_id)
    observations = observations.select_related("pupil", "author")
    return render(
        request,
        "tolerance/observation_list.html",
        {"observations": observations, "pupils": pupils, "selected_pupil": pupil_id},
    )


@login_required
def observation_detail(request, pk):
    observation = get_object_or_404(Observation, pk=pk)
    return render(request, "tolerance/observation_detail.html", {"observation": observation})


@login_required
def observation_create(request):
    school = _school_for(request.user)
    if request.method == "POST":
        form = ObservationForm(request.POST, school=school)
        if form.is_valid():
            observation = form.save(commit=False)
            observation.author = request.user
            observation.save()
            return redirect("observation_detail", pk=observation.pk)
    else:
        form = ObservationForm(school=school)
    return render(request, "tolerance/observation_form.html", {"form": form})


@login_required
def observation_edit(request, pk):
    school = _school_for(request.user)
    observation = get_object_or_404(Observation, pk=pk, pupil__school=school)
    if request.method == "POST":
        form = ObservationForm(request.POST, instance=observation, school=school)
        if form.is_valid():
            form.save()
            return redirect("observation_detail", pk=observation.pk)
    else:
        form = ObservationForm(instance=observation, school=school)
    return render(request, "tolerance/observation_form.html", {"form": form, "observation": observation})


@login_required
def dashboard(request):
    school = _school_for(request.user)
    since = date.today() - timedelta(weeks=4)
    rows = []
    alerts = []
    for pupil in Pupil.objects.filter(school=school):
        observations = Observation.objects.filter(pupil=pupil, observed_on__gte=since)
        total = observations.count()
        anxious = observations.filter(mood="anxious").count()
        withdrawn = observations.filter(mood="withdrawn").count()
        dysregulated = observations.filter(mood="dysregulated").count()
        concern = 0
        if total:
            concern = round(100 * (anxious + withdrawn + 2 * dysregulated) / (2 * total))
        if dysregulated >= 3:
            level = "high"
        elif concern >= 50:
            level = "medium"
        else:
            level = "low"
        latest = observations.first()
        rows.append(
            {
                "pupil": pupil,
                "total": total,
                "anxious": anxious,
                "withdrawn": withdrawn,
                "dysregulated": dysregulated,
                "concern": concern,
                "level": level,
                "latest": latest,
                "latest_author": latest.author.get_full_name() if latest else "",
            }
        )
        if level == "high":
            alerts.append(pupil)
    rows.sort(key=lambda r: (-r["concern"], r["pupil"].last_name))
    if alerts and request.GET.get("notify") == "1":
        names = ", ".join(str(p) for p in alerts)
        send_mail(
            "Pupils needing attention",
            f"The following pupils have three or more dysregulated observations in the last four weeks: {names}",
            None,
            [request.user.email],
        )
    return render(
        request,
        "tolerance/dashboard.html",
        {"rows": rows, "alerts": alerts, "since": since, "total_pupils": len(rows)},
    )
