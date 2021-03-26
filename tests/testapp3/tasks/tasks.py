import dramatiq


@dramatiq.actor
def example():
    pass


@dramatiq.actor(queue_name='balance')
def example():
    pass


@dramatiq.actor(queue_name='qwerty')
def example():
    pass
