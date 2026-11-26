"""The log only. Chats are not in the admin: nobody but their owner reads
them, and the owner has the chat page."""
from django.contrib import admin

from .models import ModelCall


@admin.register(ModelCall)
class ModelCallAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "model", "prompt_version", "outcome",
                    "api_calls", "input_tokens", "output_tokens")
    list_filter = ("outcome", "model", "prompt_version")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
