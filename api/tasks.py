from backend.celeryFile import app
import requests
from .views import SaveData
from dotenv import load_dotenv, find_dotenv
import os
from .models import Movie, Genre, Directors, PageInfo
from django.core.exceptions import ObjectDoesNotExist

# dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(find_dotenv())

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

def getNextPage(type):
    # Try to get the PageInfo object for the given type
    page_row = PageInfo.objects.filter(endpoint=type).first()

    # If it exists, increment the page number
    if page_row is not None: 
        page = page_row.page + 1
        page_row.page = page
        page_row.save()
    else: 
        # If it doesn't exist, create it with page 1 
        page = 1
        PageInfo.objects.create(page=page, endpoint=type)

    return page


def fetchMovieOmdbApi(OMDB_API_KEY, name) : 
    URL = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={name.replace(' ', '+')}"
    return requests.get(URL).json()

def fetchGenresListTmdbApi(TMDB_API_KEY):
    URL = f"https://api.themoviedb.org/3/genre/movie/list?language=en-US"
    HEADERS = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_API_KEY}"
    }

    return requests.get(URL, headers=HEADERS).json()


def fetchMoviesListTmdbApi(type, page, TMDB_API_KEY):
    URL = f"https://api.themoviedb.org/3/movie/{type}?language=en-US&page={page}"
    HEADERS = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_API_KEY}"
    }

    return requests.get(URL, headers=HEADERS).json()
    
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
    
    data['ratings'] = {
        'metacritics': omdbMovie.get("Metascore", 'N/A'),
        'imdb' : omdbMovie.get("imdbRating", 'N/A') 
    }
    data['contentRate'] = omdbMovie.get("Rated", 'N/A') 
    data['duration'] = omdbMovie.get("Runtime", 'N/A')
    data['imdbId']= omdbMovie.get('imdbID', None)
    data['director'] = None
    if (omdbMovie.get("Director", 'N/A')!= "N/A") : 
        director,created =  Directors.objects.get_or_create(name = omdbMovie['Director'])
        data['director'] = director

def getGenres(TMDB_API_KEY):
    data= []
    genresList = fetchGenresListTmdbApi(TMDB_API_KEY)

    if "success" in genresList and not genresList['success'] :
        return False
    
    for genre in genresList['genres'] :
        extractDataFromTmdbGenreRequest(data,genre)

    Genre.objects.bulk_create(data)
    return True

def getMovies(type,page, TMDB_API_KEY, OMDB_API_KEY):
    tmdb_movies_list = fetchMoviesListTmdbApi(type,page,TMDB_API_KEY)

    if "success" in tmdb_movies_list and not tmdb_movies_list['success'] :
        return False

    if not "results" in tmdb_movies_list : 
        return False
    
    for item in tmdb_movies_list['results']:
        if (not item.get('title',False) or Movie.objects.filter(title=item['title']).exists()) :
            continue

        data={"thumbnail":None}
        omdbResponse = fetchMovieOmdbApi(OMDB_API_KEY, item['title'])

        extractDataFromTmdbMovieRequest(data,item)
        extractDataFromOmdbMovieRequest(data, omdbResponse)

        genres = data.pop('genre', None)
        movie = Movie.objects.create(**data)

        if genres:
            genre_objects = Genre.objects.filter(id__in=genres)
            movie.genre.set(genre_objects)

    return True

def apiCall(type):
    page = getNextPage(type)
    getGenres(TMDB_API_KEY)
    getMovies(type,page,TMDB_API_KEY,OMDB_API_KEY)
            
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