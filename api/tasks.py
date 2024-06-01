from backend.celeryFile import app
import requests
from .views import SaveData
from dotenv import load_dotenv, find_dotenv
import os
from .models import Movie, Genre, Directors, PageInfo, ContentRating
from django.core.exceptions import ObjectDoesNotExist

load_dotenv(find_dotenv())

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")


def getHeaders(apiKey):
    return {
        "accept": "application/json",
        "Authorization": f"Bearer {apiKey}"
    }

def getNextPage(type):
    page_row = PageInfo.objects.filter(endpoint=type).first()
    if page_row is None: 
        page_row = PageInfo.objects.create(page=1, endpoint=type)

    return page_row.page

def incrementPage(type):
    page_row = PageInfo.objects.filter(endpoint=type).first()
    page = page_row.page + 1
    page_row.page = page
    page_row.save()

def fetchMovieOmdbApi(OMDB_API_KEY, name) : 
    URL = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={name.replace(' ', '+')}"
    return requests.get(URL).json()

def fetchGenresListTmdbApi(TMDB_API_KEY):
    URL = f"https://api.themoviedb.org/3/genre/movie/list?language=en-US"
    return requests.get(URL, headers=getHeaders(TMDB_API_KEY)).json()

def fetchMoviesListTmdbApi(type, page, TMDB_API_KEY):
    URL = f"https://api.themoviedb.org/3/movie/{type}?language=en-US&page={page}"
    return requests.get(URL, headers=getHeaders(TMDB_API_KEY)).json()
    
def extractDataFromTmdbGenreRequest(data, tmdbGenre) :
    try :
        Genre.objects.get(name=tmdbGenre['name']) 
    except ObjectDoesNotExist:
        data.append(Genre(pk=tmdbGenre['id'], name=tmdbGenre['name']))

def extractDataFromTmdbMovieRequest(data,tmdbMovie):
    data['title'] = tmdbMovie['title']
    data['poster'] = tmdbMovie['poster_path']
    data['image'] = tmdbMovie['backdrop_path']
    data['plot'] = tmdbMovie['overview']
    data['released'] = tmdbMovie['release_date']
    data['genre'] = tmdbMovie['genre_ids']
    
def extractDataFromOmdbMovieRequest(data,omdbMovie):
    if not omdbMovie : 
        return
    
    data['director'] = None
    data['contentRating'] = None
    data['imdbId']= omdbMovie.get('imdbID', None)
    data['duration'] = omdbMovie.get("Runtime", 'N/A')
    data['ratings'] = {
        'metacritics': omdbMovie.get("Metascore", 'N/A'),
        'imdb' : omdbMovie.get("imdbRating", 'N/A') 
    }
    
    if (omdbMovie.get("Rated","N/A") != "N/A") : 
        contentRating, created = ContentRating.objects.get_or_create(name = omdbMovie['Rated'])
        data['contentRating'] = contentRating

    if (omdbMovie.get("Director", 'N/A')!= "N/A") : 
        director,created =  Directors.objects.get_or_create(name = omdbMovie['Director'])
        data['director'] = director

def getTrailer(TMDB_API_KEY, movieID):
    URL = f"https://api.themoviedb.org/3/movie/{movieID}/videos"
    response = requests.get(URL, headers=getHeaders(TMDB_API_KEY)).json()

    if 'results' in response and len(response['results']) > 0: 
        return response['results'][0]
    return {'key':None} 

def getGenres(TMDB_API_KEY):
    data= []
    genresList = fetchGenresListTmdbApi(TMDB_API_KEY)

    if "success" in genresList and not genresList['success'] :
        return False
    
    for genre in genresList['genres'] :
        extractDataFromTmdbGenreRequest(data,genre)

    Genre.objects.bulk_create(data)
    return True

def getMovies(type, TMDB_API_KEY, OMDB_API_KEY):
    page = getNextPage(type)
    tmdb_movies_list = fetchMoviesListTmdbApi(type,page,TMDB_API_KEY)

    if "success" in tmdb_movies_list and not tmdb_movies_list['success'] :
        return False

    if not "results" in tmdb_movies_list : 
        return False
    
    for item in tmdb_movies_list['results']:
        if (not item.get('title',True) or Movie.objects.filter(title=item['title']).exists()) :
            continue

        data={"thumbnail":None, 'trailer':getTrailer(TMDB_API_KEY, item['id']).get('key',None)}
        omdbResponse = fetchMovieOmdbApi(OMDB_API_KEY, item['title'])

        extractDataFromTmdbMovieRequest(data,item)
        extractDataFromOmdbMovieRequest(data, omdbResponse)

        genres = data.pop('genre', None)
        movie = Movie.objects.create(**data)

        if genres:
            genre_objects = Genre.objects.filter(id__in=genres)
            movie.genre.set(genre_objects)

    incrementPage(type)
    return True

def apiCall(type):
    getGenres(TMDB_API_KEY)
    getMovies(type,TMDB_API_KEY,OMDB_API_KEY)
            
@app.task
def InTheaters():
    apiCall("now_playing")
    return True

@app.task
def MostPopularMovies():
    apiCall("popular")
    return True
    
@app.task
def ComingSoon():
    apiCall("upcoming")
    return True

@app.task 
def TopImdb():
    apiCall('top_rated')
    return True