"""The four things article 13 says an AI feature must keep: a versioned
corpus, a log of every call, the model's suggestion, and the person's
acceptance. Nothing here holds a pupil's name."""
from django.conf import settings
from django.db import models


class Corpus(models.Model):
    """One loaded version of the guidance documents. Re-loading makes a new
    one; old calls keep citing the version they used."""

    version = models.CharField(max_length=40, unique=True)
    loaded_at = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return f"Corpus {self.version}"


class Document(models.Model):
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=200)
    source = models.URLField(blank=True)
    path = models.CharField(max_length=300)

    def __str__(self):
        return self.title


class Passage(models.Model):
    """A section of a document, the unit the model is given and cites."""

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="passages")
    section = models.CharField(max_length=200)
    position = models.PositiveIntegerField()
    text = models.TextField()

    class Meta:
        ordering = ["document", "position"]

    def ref(self):
        return f"{self.document.title} / {self.section}"

    def __str__(self):
        return self.ref()


class ModelCall(models.Model):
    """Every call, whatever happened. The redacted request text is kept only
    when AI_KEEP_REQUEST_TEXT is on, under the project's retention rule."""

    OUTCOMES = [
        ("ok", "Answered"),
        ("refused", "Refused by the model"),
        ("timeout", "Timed out"),
        ("rate_limited", "Rate limited"),
        ("error", "Error"),
        ("cap", "Monthly cap reached"),
        ("no_corpus", "No corpus loaded"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="model_calls")
    school_id = models.PositiveIntegerField(db_index=True)
    pupil_ref = models.CharField(max_length=64, blank=True)
    model = models.CharField(max_length=60)
    prompt_version = models.CharField(max_length=20)
    corpus_version = models.CharField(max_length=40, blank=True)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    latency_ms = models.PositiveIntegerField(default=0)
    outcome = models.CharField(max_length=20, choices=OUTCOMES)
    grounded = models.BooleanField(default=False)
    request_id = models.CharField(max_length=64, blank=True)
    request_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["school_id", "created_at"])]

    def __str__(self):
        return f"{self.model} {self.outcome} {self.created_at:%Y-%m-%d %H:%M}"


class Suggestion(models.Model):
    """What the model said, with the passages it cited. The teacher's
    accepted text is theirs and goes onto the record, not here."""

    call = models.OneToOneField(ModelCall, on_delete=models.CASCADE, related_name="suggestion")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="suggestions")
    school_id = models.PositiveIntegerField(db_index=True)
    pupil_ref = models.CharField(max_length=64)
    question = models.TextField(help_text="Redacted before storage.")
    answer = models.TextField()
    citations = models.JSONField(default=list)
    grounded = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Suggestion {self.pk} ({'grounded' if self.grounded else 'opinion'})"
