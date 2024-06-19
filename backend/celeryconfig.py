from celery.schedules import crontab

broker_url = "redis://redis:6379/2"
broker_connection_retry_on_startup = True

#time utc
beat_schedule = {
    'InTheaters task': {
        'task': 'api.tasks.InTheaters',
        'schedule':crontab(hour='5', minute='35',day_of_week='wed,sat'),
    },
    'MostPopularMovies task':{
        'task': 'api.tasks.MostPopularMovies',
        'schedule':crontab(hour='5', minute='28',day_of_week='wed,thu,sun'),
    },
    'ComingSoon task':{
        'task': 'api.tasks.ComingSoon',
        'schedule':crontab(hour='5', minute='30',day_of_week='wed,fri,tue,sat'),
    },
    'TopImdb task':{
        'task': 'api.tasks.TopImdb',
        'schedule':crontab(hour='5', minute='32',day_of_week='wed,sun'),
    },
    'generate_and_store_cosine_similarity_dataframe_of_all_movies task':{
        'task': 'api.tasks.generate_and_store_cosine_similarity_dataframe_of_all_movies',
        'schedule':crontab(hour='10', minute='10',day_of_week='sun'),
    }
}