# Dramatiq Django Basic Exmple App

This is a Django app using `django-dramatiq[redis]` with the most basic setup. 

Here you can find the settings, actor and sending data to the actor. 

## Run locally

Run the local project with Redis `cd examples/basic && docker compose up -d` and then `python manage.py migrate && python manage.py runserver`
