import dramatiq


@dramatiq.actor
def add(x, y):
    add.logger.debug("x + y = %s", x + y)
