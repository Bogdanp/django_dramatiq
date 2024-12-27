import json
from datetime import datetime, timezone

from django.conf import settings
from django.contrib import admin
from django.utils.safestring import mark_safe
from django_dramatiq.apps import DjangoDramatiqConfig
from dramatiq.encoder import JSONEncoder

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
        message_dict = instance.message._asdict()

        # make sure we can still get a representation of the
        # kwargs payload when a non json encoder is in use
        kwargs_encoder = DjangoDramatiqConfig.select_encoder()
        if not isinstance(kwargs_encoder, JSONEncoder):
            for k, v in message_dict["kwargs"].items():
                message_dict["kwargs"][k] = f"<{v}>"

        message_details = json.dumps(message_dict, indent=4)
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
