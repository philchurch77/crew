from django.conf import settings
from django.db import models

from schools.models import Pupil


class Observation(models.Model):
    """A teacher's written observation of a pupil's behaviour or emotional state."""

    MOOD_CHOICES = [
        ("calm", "Calm"),
        ("anxious", "Anxious"),
        ("withdrawn", "Withdrawn"),
        ("dysregulated", "Dysregulated"),
    ]

    pupil = models.ForeignKey(Pupil, on_delete=models.CASCADE, related_name="observations")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="observations")
    observed_on = models.DateField()
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    body = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-observed_on", "-created_at"]

    def __str__(self):
        return f"{self.pupil} on {self.observed_on}"
