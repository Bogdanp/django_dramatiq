import json

from datetime import datetime
from django.contrib import admin
from django.utils import timezone
from django.utils.safestring import mark_safe

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    exclude = ("message_data",)
    readonly_fields = ("message_details", "traceback", "status")
    list_display = ("__str__", "status", "eta", "created_at", "updated_at", "queue_name", "actor_name")

    def queue_name(self, instance):
        return instance.message_data["queue_name"]

    def actor_name(self, instance):
        return instance.message_data["actor_name"]

    def eta(self, instance):
        timestamp = instance.message_data["options"].get("eta", instance.message_data["message_timestamp"]) / 1000
        return timezone.make_aware(datetime.utcfromtimestamp(timestamp))

    def message_details(self, instance):
        message_details = json.dumps(instance.message_data, indent=4)
        return mark_safe(f"<pre>{message_details}</pre>")

    def traceback(self, instance):
        traceback = instance.message.options.get("traceback", None)
        if traceback:
            return mark_safe(f"<pre>{traceback}</pre>")
        return None
