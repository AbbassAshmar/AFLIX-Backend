#!/bin/bash

# Start the Celery worker in the background
celery -A backend worker --loglevel=DEBUG &

# Start the dummy HTTP server
python ./celery_dummy_server.py
