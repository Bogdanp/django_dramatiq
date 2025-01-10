import dramatiq


@dramatiq.actor
def add(x, y):
    add.logger.debug(f"x + y = {x + y}")
