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

# UTC time zone by default
app.conf.beat_schedule = {
    'InTheaters task': {
        'task': 'api.tasks.InTheaters',
        'schedule':crontab(hour='3', minute='23',day_of_week='mon,sat'),
    },
    'MostPopularMovies task':{
        'task': 'api.tasks.MostPopularMovies',
        'schedule':crontab(hour='9', minute='11',day_of_week='thu,sun'),
    },
    'ComingSoon task':{
        'task': 'api.tasks.ComingSoon',
        'schedule':crontab(hour='2', minute='27',day_of_week='fri,tue,sat'),
    },
    'TopImdb task':{
        'task': 'api.tasks.TopImdb',
        'schedule':crontab(hour='6', minute='22',day_of_week='wed,sun'),
    },
    'generate_and_store_cosine_similarity_dataframe_of_all_movies task':{
        'task': 'api.tasks.generate_and_store_cosine_similarity_dataframe_of_all_movies',
        'schedule':crontab(hour='10', minute='10',day_of_week='sun'),
    }
}
