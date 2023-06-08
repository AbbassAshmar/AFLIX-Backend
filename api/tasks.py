from backend.celery import app
import requests
from .views import SaveData

ImdbApiKey = "k_ofu8b6bo"
def apiCall(name):
    imdburl = f"https://imdb-api.com/en/API/{name}/{ImdbApiKey}" #call the imdb api
    r = requests.get(imdburl).json() #parse the response to json then convert it to dictionary
    if r['errorMessage'] == '' : #check for error messages
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