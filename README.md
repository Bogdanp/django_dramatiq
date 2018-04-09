# django_dramatiq

[![Build Status](https://travis-ci.org/Bogdanp/django_dramatiq.svg?branch=master)](https://travis-ci.org/Bogdanp/django_dramatiq)
[![Test Coverage](https://api.codeclimate.com/v1/badges/d20f010978828b7530dd/test_coverage)](https://codeclimate.com/github/Bogdanp/django_dramatiq/test_coverage)
[![Maintainability](https://api.codeclimate.com/v1/badges/d20f010978828b7530dd/maintainability)](https://codeclimate.com/github/Bogdanp/django_dramatiq/maintainability)
[![PyPI version](https://badge.fury.io/py/django-dramatiq.svg)](https://badge.fury.io/py/django-dramatiq)

**django_dramatiq** is a Django app that integrates with [Dramatiq][dramatiq].


## Requirements

* [Django][django] 1.11+
* [Dramatiq][dramatiq] 0.18+


## Example

You can find an example application built with django_dramatiq [here][example].


## Installation

Use [pipenv][pipenv] (or plain pip) to install the package:

    pipenv install django_dramatiq

Add `django_dramatiq` to installed apps *before* any of your custom
apps:

``` python
import os

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
    "BROKER": "dramatiq.brokers.rabbitmq.URLRabbitmqBroker",
    "OPTIONS": {
        "url": "amqp://localhost:5672",
    },
    "MIDDLEWARE": [
        "dramatiq.middleware.Prometheus",
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Retries",
        "django_dramatiq.middleware.AdminMiddleware",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
    ]
}

# Defines which database should be used to persist Task objects when the
# AdminMiddleware is enabled.  The default value is "default".
DRAMATIQ_TASKS_DATABASE = "default"
```


## Usage

### Declaring tasks

django_dramatiq will auto-discover tasks defined in `tasks` modules in
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

### Running workers

django_dramatiq comes with a management command you can use to
auto-discover task modules and run workers:

    python manage.py rundramatiq

### Testing

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
        "django_dramatiq.middleware.AdminMiddleware",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
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

#### Cleaning up old tasks

The `AdminMiddleware` stores task metadata in a relational DB so it's
a good idea to garbage collect that data every once in a while.  You
can use the `delete_old_tasks` actor to achieve this on a cron:

``` python
delete_old_tasks.send(max_task_age=86400)
```


### Middleware

<dl>
  <dt>django_dramatiq.middleware.AdminMiddleware</dt>
  <dd>
    This middleware stores metadata about tasks in flight to a
    database and exposes them via the Django admin.
  </dd>

  <dt>django_dramatiq.middleware.DbConnectionsMiddleware</dt>
  <dd>
    This middleware takes care of closing up DB connections when
    worker threads shut down.
  </dd>
</dl>


### Usage with [django-configurations]

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


## License

django_dramatiq is licensed under Apache 2.0.  Please see
[LICENSE][license] for licensing details.

[django]: http://djangoproject.com/
[dramatiq]: https://github.com/Bogdanp/dramatiq
[example]: https://github.com/Bogdanp/django_dramatiq_example
[license]: https://github.com/Bogdanp/django_dramatiq/blob/master/LICENSE
[pipenv]: https://docs.pipenv.org
[pytest-django]: https://pytest-django.readthedocs.io/en/latest/index.html
[stubbroker]: https://dramatiq.io/reference.html#dramatiq.brokers.stub.StubBroker
[django-configurations]: https://github.com/jazzband/django-configurations/
[transactiontestcase]: https://docs.djangoproject.com/en/dev/topics/testing/tools/#django.test.TransactionTestCase
