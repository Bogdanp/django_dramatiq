import json
from datetime import datetime

from django.conf import settings
from django.contrib import admin
from django.utils import timezone
from django.utils.safestring import mark_safe

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    exclude = ("message_data",)
    readonly_fields = ("message_details", "traceback", "status", "queue_name", "actor_name")
    list_display = (
        "__str__",
        "status",
        "eta",
        "created_at",
        "updated_at",
        "queue_name",
        "actor_name",
    )
    list_filter = ("status", "created_at", "queue_name", "actor_name")
    search_fields = ("actor_name",)

    def eta(self, instance):
        timestamp = (
            instance.message.options.get("eta", instance.message.message_timestamp) / 1000
        )

        # Django expects a timezone-aware datetime if USE_TZ is True, and a naive datetime in localtime otherwise.
        tz = timezone.utc if settings.USE_TZ else None
        return datetime.fromtimestamp(timestamp, tz=tz)

    def message_details(self, instance):
        message_details = json.dumps(instance.message._asdict(), indent=4)
        return mark_safe("<pre>%s</pre>" % message_details)

    def traceback(self, instance):
        traceback = instance.message.options.get("traceback", None)
        if traceback:
            return mark_safe("<pre>%s</pre>" % traceback)
        return None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, task=None):
        return False

    def has_delete_permission(self, request, task=None):
        return False
