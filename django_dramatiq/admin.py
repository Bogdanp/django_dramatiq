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
        return instance.message.queue_name

    def actor_name(self, instance):
        return instance.message.actor_name

    def eta(self, instance):
        timestamp = instance.message.options.get("eta", instance.message.message_timestamp) / 1000
        return timezone.make_aware(datetime.utcfromtimestamp(timestamp))

    def message_details(self, instance):
        message_details = json.dumps(instance.message._asdict(), indent=4)
        return mark_safe("<pre>%s</pre>" % message_details)

    def traceback(self, instance):
        traceback = instance.message.options.get("traceback", None)
        if traceback:
            return mark_safe("<pre>%s</pre>" % traceback)
        return None
