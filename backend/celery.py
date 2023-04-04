import os 
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')


#the configuration of celery is in "settings"
#only the keys that start with CELERY_ and all CAP belong to celery conf.
app.config_from_object('django.conf:settings', namespace="CELERY") 

#autodiscover files that are named tasks
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'InTheaters task': {
        'task': 'api.tasks.InTheaters',
        'schedule':crontab(hour='5', minute='0',day_of_week='mon,thu,sun'),
        # 'schedule': crontab(hour=7, minute=30, day_of_week=1),
    },
    'MostPopularMovies task':{
        'task': 'api.tasks.MostPopularMovies',
        'schedule':crontab(hour='5', minute='0',day_of_week='tue,fri'),
    },
    'ComingSoon task':{
        'task': 'api.tasks.ComingSoon',
        'schedule':crontab(hour='5', minute='0',day_of_week='wed,sat'),
    }
}
# @app.task(bind=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')