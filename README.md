# Django Dramatiq

![Python Version](https://img.shields.io/pypi/pyversions/django-dramatiq)
![Django Versions](https://img.shields.io/pypi/frameworkversions/django/django-dramatiq)
[![Build Status](https://github.com/Bogdanp/django_dramatiq/actions/workflows/ci.yml/badge.svg)](https://github.com/Bogdanp/django_dramatiq/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/django-dramatiq.svg)](https://badge.fury.io/py/django-dramatiq)
[![License](https://img.shields.io/badge/License-Apache_2.0-orange.svg)](https://opensource.org/licenses/Apache-2.0)

Seemlessly integrate [Dramatiq][dramatiq] with your Django project!

# Contents

- [Installation](#installation)
- [Getting Started](#getting-started)
- [Testing](#testing)
- [Middleware](#middleware)
- [Advanced Usage](#advanced-usage)
- [Third-Party Support](#third-party-support)
- [Example App](#example)

## Installation

To install, ensure both Django Dramatiq and Dramatiq are installed, along with RabbitMQ:

    pip install django-dramatiq 'dramatiq[rabbitmq]'

Or with Redis:

    pip install django-dramatiq 'dramatiq[redis]'

If you would like to install with `watch`:

    pip install django-dramatiq 'dramatiq[rabbitmq, watch]'


Add `django_dramatiq` to installed apps *before* any of your custom
apps:

``` python
INSTALLED_APPS = [
    "django_dramatiq",

    "myprojectapp1",
    "myprojectapp2",
    # etc...
]
```

Configure your broker in `settings.py`:

``` python
DRAMATIQ_BROKER = {
    "BROKER": "dramatiq.brokers.rabbitmq.RabbitmqBroker", 
    "OPTIONS": {
        "url": "amqp://localhost:5672",
    },
    "MIDDLEWARE": [
        "dramatiq.middleware.Prometheus",
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Retries",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
        "django_dramatiq.middleware.AdminMiddleware",
    ]
}

# Defines which database should be used to persist Task objects when the
# AdminMiddleware is enabled.  The default value is "default".
DRAMATIQ_TASKS_DATABASE = "default"
```

## Getting Started

### Declaring tasks

Django Dramatiq will auto-discover tasks defined in `tasks` modules in
each of your installed apps.  For example, if you have an app named
`customers`, your tasks for that app should live in a module called
`customers.tasks`:

``` python
import dramatiq

from django.core.mail import send_mail

from .models import Customer

@dramatiq.actor
def email_customer(customer_id, subject, message):
    customer = Customer.get(pk=customer_id)
    send_mail(subject, message, "webmaster@example.com", [customer.email])
```

You can override the name of the `tasks` module by setting one or more
names in settings:

``` python
DRAMATIQ_AUTODISCOVER_MODULES = ["tasks", "services"]
```

### Running workers

Django Dramatiq comes with a management command you can use to
auto-discover task modules and run workers:

```sh
    python manage.py rundramatiq
```

By default, `rundramatiq` will adjust the number of processes/threads used
by Dramatiq based on the number of detected CPUs: one process will be launched
per CPU, and each process will have 8 worker threads.

The default number of processes, threads per process can be overridden through
environment variables, which take precedence over the defaults:

```sh
    export DRAMATIQ_NPROCS=2 DRAMATIQ_NTHREADS=2
    python manage.py rundramatiq
```

Or alternatively through command line arguments, which take precedence over the
defaults and any environment variables:

```sh
    python manage.py rundramatiq -p 2 -t 2
```

This is useful e.g. to facilitate faster Dramatiq restarts in your development
environment.

If your project for some reason has apps with modules named `tasks` that
are not intended for use with Dramatiq, you can ignore them:

``` python
DRAMATIQ_IGNORED_MODULES = (
    'app1.tasks',
    'app2.tasks',
    'app3.tasks.utils',
    'app3.tasks.utils.*',
    ...
)
```

The wildcard detection will ignore all sub modules from that point on. You
will need to ignore the module itself if you don't want the `__init__.py` to
be processed.

### Results Backend

You may also configure a result backend:

``` python
DRAMATIQ_RESULT_BACKEND = {
    "BACKEND": "dramatiq.results.backends.redis.RedisBackend",
    "BACKEND_OPTIONS": {
        "url": "redis://localhost:6379",
    },
    "MIDDLEWARE_OPTIONS": {
        "result_ttl": 1000 * 60 * 10
    }
}
```

## Testing

You should have a separate settings file for test.  In that file,
overwrite the broker to use Dramatiq's [StubBroker][stubbroker]:

``` python
DRAMATIQ_BROKER = {
    "BROKER": "dramatiq.brokers.stub.StubBroker",
    "OPTIONS": {},
    "MIDDLEWARE": [
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Pipelines",
        "dramatiq.middleware.Retries",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
        "django_dramatiq.middleware.AdminMiddleware",
    ]
}
```

#### Using [pytest-django][pytest-django]

In your `conftest` module set up fixtures for your broker and a
worker:

``` python
import dramatiq
import pytest

@pytest.fixture
def broker():
    broker = dramatiq.get_broker()
    broker.flush_all()
    return broker

@pytest.fixture
def worker(broker):
    worker = dramatiq.Worker(broker, worker_timeout=100)
    worker.start()
    yield worker
    worker.stop()
```

In your tests, use those fixtures whenever you want background tasks
to be executed:

``` python
def test_customers_can_be_emailed(transactional_db, broker, worker, mailoutbox):
    customer = Customer(email="jim@gcpd.gov")
    # Assuming "send_welcome_email" enqueues an "email_customer" task
    customer.send_welcome_email()

    # Wait for all the tasks to be processed
    broker.join("default")
    worker.join()

    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Welcome Jim!"
```


> [!NOTE]  
> If your tests rely on the results of the actor, you may experience inconsistent results. Due to the nature of the worker and test running in seperate threads, the test DB state may be different. 
> 
> To solve this you need to add the addtional `@pytest.mark.django_db(transaction=True)` decorator. 

#### Using unittest

A simple test case has been provided that will automatically set up the
broker and worker for each test, which are accessible as attributes on
the test case. Note that `DramatiqTestCase` inherits
[`django.test.TransactionTestCase`][transactiontestcase].


```python
from django.core import mail
from django.test import override_settings
from django_dramatiq.test import DramatiqTestCase


class CustomerTestCase(DramatiqTestCase):

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_customers_can_be_emailed(self):
        customer = Customer(email="jim@gcpd.gov")
        # Assuming "send_welcome_email" enqueues an "email_customer" task
        customer.send_welcome_email()

        # Wait for all the tasks to be processed
        self.broker.join(customer.queue_name)
        self.worker.join()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Welcome Jim!")
```


## Advanced Usage

### Cleaning up old tasks

The `AdminMiddleware` stores task metadata in a relational DB so it's
a good idea to garbage collect that data every once in a while.  You
can use the `delete_old_tasks` actor to achieve this on a cron:

``` python
from django_dramatiq.tasks import delete_old_tasks

delete_old_tasks.send(max_task_age=60 * 60 * 24)
```


## Middleware

<dl>
  <dt>django_dramatiq.middleware.DbConnectionsMiddleware</dt>
  <dd>
    This middleware is vital in taking care of closing expired
    connections after each message is processed.
  </dd>

  <dt>django_dramatiq.middleware.AdminMiddleware</dt>
  <dd>
    This middleware stores metadata about tasks in flight to a
    database and exposes them via the Django admin.
  </dd>
</dl>

### Custom keyword arguments to Middleware

Some middleware classes require dynamic arguments.  An example of this
would be the backend argument to `dramatiq.middleware.GroupCallbacks`.

To do this, you might add the middleware to your `settings.py`:

```python
DRAMATIQ_BROKER = {
    ...
    "MIDDLEWARE": [
        ...
        "dramatiq.middleware.GroupCallbacks",
        ...
    ]
    ...
}
```

Next, you need to extend `DjangoDramatiqConfig` to provide the
arguments for this middleware:

```python
from django_dramatiq.apps import DjangoDramatiqConfig


class CustomDjangoDramatiqConfig(DjangoDramatiqConfig):
    @classmethod
    def middleware_groupcallbacks_kwargs(cls):
        return {"rate_limiter_backend": cls.get_rate_limiter_backend()}
```

Notice the naming convention, to provide arguments to
`dramatiq.middleware.GroupCallbacks` you need to add a `@classmethod`
with the name `middleware_<middleware_name>_kwargs`, where
`<middleware_name>` is the lowercase name of the middleware.

Finally, add the custom app config to your `settings.py`, replacing
the existing `django_dramatiq` app config:

```python
INSTALLED_APPS = [
    ...
    "yourapp.apps.CustomDjangoDramatiqConfig",
    ...
]
```


## Third-Party Support

#### Usage with [django-configurations]

To use django_dramatiq together with [django-configurations] you need
to define your own `rundramatiq` command as a subclass of the one in
this package.

In `YOURPACKAGE/management/commands/rundramatiq.py`:

``` python
from django_dramatiq.management.commands.rundramatiq import Command as RunDramatiqCommand


class Command(RunDramatiqCommand):
    def discover_tasks_modules(self):
        tasks_modules = super().discover_tasks_modules()
        tasks_modules[0] = "YOURPACKAGE.dramatiq_setup"
        return tasks_modules
```

And in `YOURPACKAGE/dramatiq_setup.py`:

``` python
import django

from configurations.importer import install

install(check_options=True)
django.setup()
```

## Example

You can find an example application built with Django Dramatiq [here](/examples/basic/README.md).


[dramatiq]: https://github.com/Bogdanp/dramatiq
[pytest-django]: https://pytest-django.readthedocs.io/en/latest/index.html
[stubbroker]: https://dramatiq.io/reference.html#dramatiq.brokers.stub.StubBroker
[django-configurations]: https://github.com/jazzband/django-configurations/
[transactiontestcase]: https://docs.djangoproject.com/en/dev/topics/testing/tools/#django.test.TransactionTestCase
