import logging

import dramatiq

from django_dramatiq.models import Task


def test_race_condition_after_enqueue_executes_after_completion(
        transactional_db, broker, worker, caplog):
    """Test race condition where after_enqueue executes after task completion.
    
    This test simulates the race condition described in issue #154 by creating
    a delayed task and manually calling after_enqueue after the task completes.
    
    Expected behavior:
    - Task completes normally and reaches DONE status  
    - Manual after_enqueue call attempts to set ENQUEUED status after completion
    - MessageStatusTransitionError is caught and logged
    - Task status remains DONE (not corrupted)
    """
    from django_dramatiq.middleware import AdminMiddleware
    
    # Define simple test actor
    @dramatiq.actor  
    def quick_task():
        """Simple task that completes quickly."""
        return "completed"
    
    # Enable debug logging to capture transition error messages
    with caplog.at_level(logging.DEBUG, logger='django_dramatiq.AdminMiddleware'):
        
        # ACT - Send task with delay to prevent immediate execution
        message = quick_task.send_with_options(delay=100)  # 100ms delay
        
        # Immediately process the task to simulate completion before after_enqueue
        broker.join(quick_task.queue_name, fail_fast=True)
        worker.join()
        
        # Verify task completed
        task = Task.tasks.get(id=message.message_id)
        assert task.status == Task.STATUS_DONE, f"Task should be DONE, got {task.status}"
        
        # Now manually trigger after_enqueue to simulate race condition
        admin_middleware = AdminMiddleware()
        admin_middleware.after_enqueue(broker, message, delay=None)
        
        # ASSERT - Verify expected outcomes
        
        # Refresh from database to ensure after_enqueue didn't corrupt status
        task.refresh_from_db()
        assert task.status == Task.STATUS_DONE, (
            f"Task status should remain DONE after delayed after_enqueue, got {task.status}"
        )
        
        # Verify that transition error was logged
        transition_error_logged = any(
            "Task status transition ignored" in record.message and
            "Incorrect flow" in record.message
            for record in caplog.records
            if record.name == 'django_dramatiq.AdminMiddleware'
        )
        
        assert transition_error_logged, (
            "AdminMiddleware should log transition error when after_enqueue "
            "attempts invalid DONE -> ENQUEUED transition"
        )
