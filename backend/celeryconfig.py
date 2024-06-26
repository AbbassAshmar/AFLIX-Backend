from celery.schedules import crontab
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

broker_url =  os.getenv("QUEUE_REDIS_URL")
broker_connection_retry_on_startup = True
worker_concurrency = 1
worker_prefetch_multiplier = 1

#time utc
beat_schedule = {
    'InTheaters task': {
        'task': 'api.tasks.InTheaters',
        'schedule':crontab(hour='5', minute='13',day_of_week='wed,sat'),
    },
    'MostPopularMovies task':{
        'task': 'api.tasks.MostPopularMovies',
        'schedule':crontab(hour='5', minute='55',day_of_week='mon'),
    },
    'ComingSoon task':{
        'task': 'api.tasks.ComingSoon',
        'schedule':crontab(hour='8', minute='21',day_of_week='thu,sun'),
    },
    'TopImdb task':{
        'task': 'api.tasks.TopImdb',
        'schedule':crontab(hour='4', minute='5',day_of_week='tue'),
    },
    'generate_and_store_cosine_similarity_dataframe_of_all_movies task':{
        'task': 'api.tasks.generate_and_store_cosine_similarity_dataframe_of_all_movies',
        'schedule':crontab(hour='10', minute='10',day_of_week='fri'),
    }
}