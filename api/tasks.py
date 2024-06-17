from backend.celeryFile import app
import requests
from dotenv import load_dotenv, find_dotenv
import os
from .models import Movie, Genre, Directors, PageInfo, ContentRating
from django.core.exceptions import ObjectDoesNotExist
from .services import MovieCosineSimilarityService

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

    print(page_row.page)
    return page_row.page

def incrementPage(type):
    page_row = PageInfo.objects.filter(endpoint=type).first()
    print(f"{page_row.page}--------------------------------------- page row increment")
    page_row.page += 1
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
    data['genres'] = tmdbMovie['genre_ids']
    
def extractDataFromOmdbMovieRequest(data,omdbMovie):
    if not omdbMovie : 
        return
    
    data['director'] = None
    data['content_rating'] = None
    data['imdbId']= omdbMovie.get('imdbID', None)
    data['duration'] = omdbMovie.get("Runtime",None)
    data['ratings'] = {
        'metacritics': omdbMovie.get("Metascore",None),
        'imdb' : omdbMovie.get("imdbRating",None) 
    }
    
    if (omdbMovie.get("Rated","N/A") != "N/A") : 
        contentRating, created = ContentRating.objects.get_or_create(name = omdbMovie['Rated'])
        data['content_rating'] = contentRating

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
    print("------------here ----------------------")
    print(tmdb_movies_list)
    if "success" in tmdb_movies_list and not tmdb_movies_list['success'] :
        print("----------success----------")
        return False

    if not "results" in tmdb_movies_list : 
        print("----------not results----------")
        return False
    
    for item in tmdb_movies_list['results']:
        if not item.get('title',True) or Movie.objects.filter(title=item['title']).exists() :
            print("--------------not title------------")
            continue

        data={"thumbnail":None, 'trailer':getTrailer(TMDB_API_KEY, item['id']).get('key',None)}
        omdbResponse = fetchMovieOmdbApi(OMDB_API_KEY, item['title'])

        extractDataFromTmdbMovieRequest(data,item)
        extractDataFromOmdbMovieRequest(data, omdbResponse)

        try :
            genres = data.pop('genres', None)
            movie = Movie.objects.create(**data)
            print(movie)
            print('--------------------no except------------------------')
        except Exception as e:
            print(e)
            continue

        if genres:
            genre_objects = Genre.objects.filter(id__in=genres)
            movie.genres.set(genre_objects)

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

@app.task
def generate_and_store_cosine_similarity_dataframe_of_all_movies() : 
    return MovieCosineSimilarityService.generate_and_store_dataframe_of_all_movies()

@app.task
def generate_and_store_cosine_similarity_dataframe_row_of_movie(id) : 
    return MovieCosineSimilarityService.generate_and_store_dataframe_row_of_movie(id)

    