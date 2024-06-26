#!/bin/bash

# Start the Celery worker in the background
celery -A backend beat -s ./celery_beat --scheduler django_celery_beat.schedulers:DatabaseScheduler &

# Start the dummy HTTP server
python ./celery_beat_dummy_server.py
