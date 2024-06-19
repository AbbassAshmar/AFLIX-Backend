import os 
from celery import Celery
from celery.schedules import crontab


# set env var DJANGO_SETTINGS_MODULE=backend.settings for django to find settings
# ensure that the Django settings are loaded into the environment as soon as the Celery worker starts
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# create celery instance
app = Celery('backend')


#the configuration of celery is in "celeryconfig.py"
app.config_from_object('backend.celeryconfig')

#Celery will look for a tasks.py file in each of the applications listed in the INSTALLED_APPS setting of Django 
app.autodiscover_tasks(['api.tasks'])
