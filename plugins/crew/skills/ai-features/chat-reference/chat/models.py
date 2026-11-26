"""A stored conversation with an assistant, and the log article 13 asks
for. Nothing here names a pupil: what a person types is theirs, kept as
typed, and deleted with the chat."""
from django.conf import settings
from django.db import models


class ChatSessionQuerySet(models.QuerySet):
    def for_user(self, user):
        """Every read path starts here (article 1)."""
        return self.filter(user=user)


class ChatSession(models.Model):
    """One conversation. Ownership lives here: views fetch it through
    ``for_user``, so an edited URL cannot reach another person's chat.
    Deleting a user deletes their chats: a chat means nothing apart from
    its owner."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions")
    # Random, not the PK; the ownership filter is what protects it.
    session_key = models.CharField(max_length=100)
    # TextField: a guessed max_length truncates typed text (article 6).
    title = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ChatSessionQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "session_key"], name="unique_session_key_per_user")
        ]
        ordering = ["-updated_at"]

    def __str__(self):
        # Never content: the admin shows __str__ in headings.
        return f"Chat {self.pk}"

    def label(self, limit):
        """The given title, else the opening message cut to ``limit``."""
        if self.title:
            return self.title
        first = self.turns.filter(role=ChatTurn.ROLE_USER).order_by("timestamp", "pk").first()
        if first is None:
            return "Untitled chat"
        text = first.content
        return text[: limit - 3] + "..." if len(text) > limit else text


class ChatTurn(models.Model):
    """One message. ``content`` is never truncated, stripped or defaulted
    over."""

    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_CHOICES = [(ROLE_USER, "User"), (ROLE_ASSISTANT, "Assistant")]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="turns")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp", "pk"]
        indexes = [models.Index(fields=["session", "timestamp"])]

    def __str__(self):
        return f"{self.role} turn {self.pk}"


class ToolCall(models.Model):
    """One look-up behind a reply: where what it says came from. Saved with
    the turn and deleted with it."""

    turn = models.ForeignKey(ChatTurn, on_delete=models.CASCADE, related_name="tool_calls")
    sequence = models.PositiveSmallIntegerField()
    # No choices: chat/tools.py is the one home of the tool set.
    tool_name = models.CharField(max_length=64)
    input = models.JSONField()
    result = models.JSONField()
    # A label a person can read, e.g. "Attendance guidance 2026-09".
    source = models.TextField(blank=True)
    is_error = models.BooleanField(default=False)

    class Meta:
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(fields=["turn", "sequence"], name="unique_tool_call_sequence_per_turn")
        ]

    def __str__(self):
        return f"{self.tool_name} #{self.sequence}"


class ModelCall(models.Model):
    """Every reply asked for, whatever happened (article 13): who, when,
    which model and prompt, what it cost, how it ended. Never content, so
    it outlives the chat it belonged to."""

    OUTCOMES = [
        ("ok", "Answered"),
        ("refused", "Refused by the model"),
        ("cut_short", "Hit the length limit"),
        ("tool_limit", "Needed too many look-ups"),
        ("empty", "No reply came back"),
        ("error", "Error"),
        ("disconnected", "The browser went away"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="chat_model_calls")
    session = models.ForeignKey(ChatSession, null=True, on_delete=models.SET_NULL, related_name="model_calls")
    model = models.CharField(max_length=60)
    prompt_version = models.CharField(max_length=20)
    api_calls = models.PositiveSmallIntegerField(default=0)
    tool_calls = models.PositiveSmallIntegerField(default=0)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    cache_read_tokens = models.PositiveIntegerField(default=0)
    latency_ms = models.PositiveIntegerField(default=0)
    outcome = models.CharField(max_length=20, choices=OUTCOMES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self):
        return f"{self.model} {self.outcome} at {self.created_at:%Y-%m-%d %H:%M}"
