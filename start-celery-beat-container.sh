#!/bin/bash

# Start the Celery worker in the background
celery -A backend beat -s ./celery_beat &

# Start the dummy HTTP server
python ./celery_beat_dummy_server.py
