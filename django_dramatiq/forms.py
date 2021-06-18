import json
import math
import datetime
from collections import Counter

from django import forms

from . import models


def _get_actor_choices() -> ((str, str),):
    return (('', '<Actor>'),) + tuple(
        (i, i) for i in models.Task.tasks.values_list('actor_name', flat=True).distinct().order_by('actor_name')
    )


def _get_queue_choices() -> ((str, str),):
    return (('', '<Queue>'),) + tuple(
        (i, i) for i in models.Task.tasks.values_list('queue_name', flat=True).distinct().order_by('queue_name')
    )


def _now_dt() -> str:
    return datetime.datetime.now().strftime("%d.%m.%Y %H:%M")


def _four_hours_ago() -> str:
    return (datetime.datetime.now() - datetime.timedelta(hours=4)).strftime("%d.%m.%Y %H:%M")


class DramatiqLoadGraphForm(forms.Form):
    start_date = forms.DateTimeField(
        label='Period start',
        widget=forms.DateTimeInput(
            attrs={'placeholder': 'Period start', 'style': 'width: 9rem;', 'maxlength': '16'}
        ),
        initial=_four_hours_ago
    )
    end_date = forms.DateTimeField(
        label='Period end',
        widget=forms.DateTimeInput(
            attrs={'placeholder': 'Period end', 'style': 'width: 9rem;', 'maxlength': '16'}
        ),
        initial=_now_dt
    )
    time_interval = forms.IntegerField(label='Interval sec', initial=10, max_value=60 * 60 * 24)
    queue = forms.ChoiceField(choices=_get_queue_choices, required=False, label='Queue')
    actor = forms.ChoiceField(choices=_get_actor_choices, required=False, label='Actor')
    status = forms.ChoiceField(choices=[('', '<All statuses>')] + models.Task.STATUSES, required=False,
                               initial=models.Task.STATUS_DONE, label='Status')

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date', None)
        end_date = cleaned_data.get('end_date', None)
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError('Period start date is greater than the period end date')
            if (end_date - start_date) > datetime.timedelta(days=3):
                raise forms.ValidationError('The maximum date range is 3 days')
        return cleaned_data

    def get_graph_data(self) -> dict:
        cd = self.cleaned_data
        start_date = cd['start_date']
        end_date = cd['end_date']
        time_tick = cd['time_interval']
        actor = cd.get('actor')
        queue = cd.get('queue')
        status = cd.get('status')
        # get qs
        task_qs = models.Task.tasks.filter(created_at__gte=start_date, created_at__lte=end_date).order_by('updated_at')
        if actor:
            task_qs = task_qs.filter(actor_name=actor)
        if queue:
            task_qs = task_qs.filter(queue_name=queue)
        if status:
            task_qs = task_qs.filter(status=status)
        if not task_qs.count():
            return {"empty_qs": True}
        categories = []
        # dt: a list of actors that worked at this time
        actor_wt_by_ticks = {(start_date + datetime.timedelta(seconds=i)).strftime("%Y-%m-%d %H:%M:%S"): []
                             for i in range(0, int((end_date - start_date).total_seconds() + 1), time_tick)}
        for task in task_qs:
            if (task.updated_at - task.created_at).days >= 1:
                # miss tasks that "work" for more than a day (most likely an error)
                continue
            if task.actor_name not in categories:
                categories.append(task.actor_name)
            actor_work_secs = (task.updated_at - task.created_at).seconds
            if actor_work_secs == 0:
                # show momental
                actor_work_secs = 1
            # seconds to next tick interval
            stonti = math.ceil(task.created_at.second / time_tick) * time_tick - task.created_at.second
            start_time = (task.created_at + datetime.timedelta(seconds=stonti)).replace(microsecond=0)
            # what ticks should this actor be assigned to
            for sec in range(0, math.ceil(actor_work_secs / time_tick)):
                calculating_dt = start_time + datetime.timedelta(seconds=time_tick * sec)
                if calculating_dt > end_date:
                    # actor can run longer than the final dt of the graph
                    continue
                else:
                    timestamp = (start_time + datetime.timedelta(seconds=time_tick * sec)).strftime("%Y-%m-%d %H:%M:%S")
                    actor_wt_by_ticks[timestamp].append(task.actor_name)
        categories = sorted(categories, reverse=True)
        working_actors_count = [[] for _ in categories]
        dates = []
        for date, actors in actor_wt_by_ticks.items():
            actors_count = Counter(actors)
            dates.append(date)
            if actors_count:
                for i, items in enumerate(categories):
                    if items in set(actors):
                        working_actors_count[i].append(actors_count[items])
                    else:
                        working_actors_count[i].append(None)
            else:
                for i, _ in enumerate(categories):
                    working_actors_count[i].append(None)
        graph_title = ', '.join(
            '{}: {}'.format(self.fields[key].label, value) for key, value in cd.items() if value != '')
        return {
            "categories": json.dumps(categories),
            "working_actors_count": json.dumps(working_actors_count),
            "dates": json.dumps(dates),
            'graph_height': json.dumps(200 + len(categories) * 25),
            'graph_title': json.dumps(graph_title),
            "empty_qs": False
        }
