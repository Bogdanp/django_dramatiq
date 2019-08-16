import abc
import json
from datetime import datetime

import dramatiq
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from django.utils.safestring import mark_safe

from .models import Task


class TaskFilter(abc.ABC, SimpleListFilter):

    @property
    def declared_broker_objects(self):
        broker = dramatiq.get_broker()
        return {
            "actor_name": broker.get_declared_actors(),
            "queue_name": broker.get_declared_queues().union(broker.get_declared_delay_queues())
        }

    def lookups(self, request, model_admin):
        lookup_choices = self.declared_broker_objects[self.parameter_name]
        return [(name, "{} (slow)".format(name)) for name in lookup_choices]
    
    def queryset(self, request, queryset):
        if self.value():
            filter_ids = (
                str(task.id) for task in queryset if getattr(task.message, self.parameter_name) == self.value()
            )
            return queryset.filter(id__in=filter_ids)

        return queryset


class QueueNameFilter(TaskFilter):
    title = "queue_name"
    parameter_name = "queue_name"


class ActorNameFilter(TaskFilter):
    title = "actor_name"
    parameter_name = "actor_name"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    exclude = ("message_data",)
    readonly_fields = ("message_details", "traceback", "status")
    list_display = ("__str__", "status", "eta", "created_at", "updated_at", "queue_name", "actor_name")
    list_filter = ("status", QueueNameFilter, ActorNameFilter)

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

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, task=None):
        return False

    def has_delete_permission(self, request, task=None):
        return False
