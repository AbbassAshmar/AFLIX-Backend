from backend.celery import app
import requests
from .views import SaveData
from dotenv import load_dotenv
import os

load_dotenv('../')
IMDB_API_KEY = os.getenv("IMDB_API_KEY")

# https://api.themoviedb.org/3/movie/popular?language=en-US&page=1


def apiCall(name):
    imdburl = f"https://imdb-api.com/en/API/{name}/{IMDB_API_KEY}" 
    r = requests.get(imdburl).json()
    if r['errorMessage'] == '' :
        for item in r["items"][:40] :
            SaveData(item)
            
@app.task
def InTheaters():
    apiCall("InTheaters")
    return True

@app.task
def MostPopularMovies():
    apiCall("MostPopularMovies")
    return True
    
@app.task
def ComingSoon():
    apiCall("ComingSoon")
    return True

@app.task 
def TopImdb():
    apiCall('Top250Movies')
    return True