import dramatiq


@dramatiq.actor
def delete_old_tasks(max_task_age=86400):
    """This task deletes all tasks older than `max_task_age` from the
    database.
    """
    from .models import Task
    Task.tasks.delete_old_tasks(max_task_age)
