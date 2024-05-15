from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework import status
import requests
from .serializers import *
from .models import *
from rest_framework.authtoken.models import Token
from django.core.exceptions import ObjectDoesNotExist
from datetime import date
import threading
from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q 
from django.db.models import Count
from authentication.views import get_object_or_404
from dotenv import load_dotenv
import os

load_dotenv('../')

OMDB_API_KEY = os.getenv("OMDB_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# {
#     "adult": false,
#     "backdrop_path": "/icmmSD4vTTDKOq2vvdulafOGw93.jpg",
#     "genre_ids": [
#         28,
#         878
#     ],
#     "id": 603,
#     "original_language": "en",
#     "original_title": "The Matrix",
#     "overview": "Set in the 22nd century, The Matrix tells the story of a computer hacker who joins a group of underground insurgents fighting the vast and powerful computers who now rule the earth.",
#     "popularity": 480.776,
#     "poster_path": "/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
#     "release_date": "1999-03-31",
#     "title": "The Matrix",
#     "video": false,
#     "vote_average": 8.215,
#     "vote_count": 24865
# },

{"Title":"Fallout",
 "Year":"2024–",
 "Rated":"TV-MA",
 "Released":"10 Apr 2024",
 "Runtime":"N/A",
 "Genre":"Action, Adventure, Drama",
 "Director":"N/A",
 "Writer":"Geneva Robertson-Dworet, Graham Wagner",
 "Actors":"Ella Purnell, Aaron Moten, Walton Goggins",
 "Plot":"In a future, post-apocalyptic Los Angeles brought about by nuclear decimation, citizens must live in underground bunkers to protect themselves from radiation, mutants and bandits.",
 "Language":"English",
 "Country":"United States",
 "Awards":"N/A",
 "Poster":"https://m.media-amazon.com/images/M/MV5BN2EwNjFhMmEtZDc4YS00OTUwLTkyODEtMzViMzliZWIyMzYxXkEyXkFqcGdeQXVyMjkwOTAyMDU@._V1_SX300.jpg",
 "Ratings":[{"Source":"Internet Movie Database","Value":"8.7/10"}],
 "Metascore":"N/A",
 "imdbRating":"8.7",
 "imdbVotes":"40,394",
 "imdbID":"tt12637874",
 "Type":"series",
 "totalSeasons":"1",
 "Response":"True"}

# "title":Apidata["title"] //
# "trailer":trailer
# "image":image //
# "thumbnail":thumbnail 
# "imdbId":Apidata['id']
# "poster":poster //
# "ratings":{"imdb":imdb , "metacritics":meta} // 
# "plot":plot //
# "contentRate":rating //
# "duration":duration
# "released":released //
# "genre":genres_id //
# "director":director.pk //

# OMDB_URL = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={Apidata['id']}"

# Videos_TMDB_URL = https://api.themoviedb.org/3/movie/{movie_id}/videos //https://www.youtube.com/watch?v={key}
# GENRES_LIST_TMDB_URL = https://api.themoviedb.org/3/genre/movie/list?language=en-US
# POPULAR_TMDB_URL = https://api.themoviedb.org/3/movie/popular?language=en-US&page=1
# UPCOMING_TMDB_URL = https://api.themoviedb.org/3/movie/upcoming?language=en-US&page=1
# TOPRATED_TMDB_URL = https://api.themoviedb.org/3/movie/top_rated?language=en-US&page=1
# NOWPLAYING_TMDB_URL = https://api.themoviedb.org/3/movie/now_playing?language=en-US&page=1


def fetchMovieOmdbApi(OMDB_API_KEY, name) : 
    URL = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={name.replace(" ", "+")}"
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

    if not genresList.get('success', True) :
        return False
    
    for genre in genresList['genres'] :
        extractDataFromTmdbGenreRequest(data,genre)

    Genre.objects.bulk_create(data)


def getMovies(type,page, TMDB_API_KEY, OMDB_API_KEY):
    tmdb_movies_list = fetchMoviesListTmdbApi(type,page,TMDB_API_KEY)
    
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



def SaveData(Apidata):
    url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={Apidata['id']}"
    omdbCall = requests.get(url).json()

    if omdbCall['Response'] == 'False':
        add_to_omdb = ["Director","Plot","Runtime","Released","Poster","imdbRating","Genre"]
        for i in add_to_omdb :
            omdbCall[i]= "N/A" #if omdbCall is False, add these to it and set them 'N/A'

    dir = Apidata["crew"].split(",")[0].replace("(dir.)",'') if 'crew' in Apidata else Apidata["directors"] 
    if dir == None:
        dir = omdbCall["Director"]

    dir = dir.split(",")[0] if ',' in dir else dir
    director, created = Directors.objects.get_or_create(name = dir) #create the director if not found else get it 
    genreList = []
    response_genre =Apidata["genres"].split(", ") if 'genres' in Apidata else omdbCall["Genre"].split(", ") # get genre list 

    for genre in response_genre:
        try :
            Genre.objects.get(name=genre) # if the genre is not in the db, add it to another list of dictionaries(genreList)
        except ObjectDoesNotExist:
            genreList += [{"name":genre}]
    if len(genreList) >0 : # check if there is genre to be added to the db 
        genres = GenresSerializer(data=genreList,many=True)
        if genres.is_valid():
            genres.save() # save the genres to the db the need to be added 

    try :
        Movie.objects.get(title = Apidata["title"]) # check if the the movie is in the db .
    # if it doesn't get the genres ids and director id of it + all the other data from the omdb and imdb api calls
    except Exception as e: 
       
        genres_ = Genre.objects.filter(name__in =response_genre) 
        director = Directors.objects.get(name=dir)
        genres_id = [genre.id for genre in genres_]
        meta =''
        if "metacriticRating" in Apidata : #check in which api meta score is available and save it in meta variable
            meta = Apidata["metacriticRating"]
        elif "Metascore" in omdbCall:
            meta = omdbCall["Metascore"]
        try:
            float(meta) # if meta is not a number , set it to "N/A"
        except (ValueError,TypeError):
            meta="N/A"
        #check in which api plot is available and save it in plot variable
        plot = omdbCall["Plot"] if ("plot" not in Apidata or Apidata["plot"] == None) else Apidata['plot']
        if len(plot) ==0 : #if the value of plot is 0, set it to none, in apis it could be empty string.
            plot="N/A"
        #check in which api runtime is available and save it in duration variable
        duration= omdbCall["Runtime"] if ("runtimeMins" not in Apidata or Apidata["runtimeMins"] == None) else Apidata["runtimeMins"]
        duration= duration.split(' ')[0]
        try:
            int(duration) #if duration is not a number , set it to "N/A"
        except (ValueError,TypeError):
            duration=0
        #check in which api released is available and save it in released variable
        released = omdbCall["Released"] if ("releaseState" not in Apidata or Apidata["releaseState"] == None) else Apidata["releaseState"]
        #check in which api content rate is available and save it in rating variable
        if "contentRating" not in Apidata :
            rating = (omdbCall["Rated"] if "Rated" in omdbCall else "N/A")
        else:
            try :
                rating=Apidata["contentRating"]
            except:
                pass
        #check in which api imdb rating is available and save it in imdb variable
        imdb = omdbCall["imdbRating"] if ("imDbRating" not in Apidata or Apidata["imDbRating"] == "null") else Apidata["imDbRating"]
        try :
            imdb = float(imdb)#if imdb is not a number ,set it to "N/A"
        except (ValueError,TypeError) :
            imdb="N/A"
        if "Poster" not in omdbCall or omdbCall["Poster"] =="N/A": # if theres no poster in omdb api
            url = f"http://www.omdbapi.com/?apikey=b6661a6a&t={Apidata['title']}"#send a request to another endpoint to get the poster
            new_omdbCall = requests.get(url).json()
            # check if the call succeeds and the poster is available save it in a variable
            if  new_omdbCall['Response'] != 'False' and new_omdbCall["Poster"] !="N/A" : 
                    poster = new_omdbCall["Poster"]
            else :
                poster = Apidata["image"]
        else : # if the poster is already available, save it in poster variable
            poster = omdbCall["Poster"]
        if poster =="N/A" or poster==None: # if the poster is not available , set it to a default poster
            poster = "https://imdb-api.com/images/128x176/nopicture.jpg"

        # get the trailer and the thumbnail of a movie from another endpoint
        trailerCall = requests.get(f"https://imdb-api.com/en/API/Trailer/{TMDB_API_KEY}/{Apidata['id']}").json()
        if trailerCall['errorMessage'] =="":
            trailer = trailerCall["linkEmbed"] 
            thumbnail = trailerCall["thumbnailUrl"]
        else : 
            trailer = "https://imdb-api.com/images/128x176/nopicture.jpg"
            thumbnail = "https://imdb-api.com/images/128x176/nopicture.jpg"

        # get the image of a movie from another endpoint
        imageCall = requests.get(f"https://imdb-api.com/en/API/Images/{TMDB_API_KEY}/{Apidata['id']}/Short").json()
        if imageCall['errorMessage'] =="" and len(imageCall['items'])>1 :
            image = imageCall['items'][1]["image"]
        else : 
            image = "https://imdb-api.com/images/128x176/nopicture.jpg"

        data = {"title":Apidata["title"], # create the data dictionary of all the variables created 
        "trailer":trailer,
        "image":image,
        "thumbnail":thumbnail,
        "imdbId":Apidata['id'],
        "poster":poster,
        "ratings":{"imdb":imdb,"metacritics":meta},
        "plot":plot,
        "contentRate":rating,
        "duration":duration,
        "released":released,
        "genre":genres_id,
        "director":director.pk}

        movieSer = MoviesSerializer(data=data) # create the unexisting movie 
        if movieSer.is_valid():
            movieSer.save()
        else:
            return Response({"error" :movieSer.errors}, status=status.HTTP_404_NOT_FOUND)

def callApi (name): 
    imdburl = f"https://imdb-api.com/en/API/{name}/{TMDB_API_KEY}" #call the imdb api
    r = requests.get(imdburl).json() #parse the response to json then convert it to dictionary
    if r['errorMessage'] == '' : #check for error messages
        for item in r["items"][:20] :
            SaveData(item)
        return True
    else :
        return False

event = threading.Event() # Create an Event to control the timimg of the thread
def setInterval(func,time,name):
    while True :
        for n in name :
            func(n) # call the function responsible for calling an api at one of the endpoints
            event.wait(time) # wait for event.set(), if given wait for it then run the function
        
# asign a function to thread, and specify the arguments in args=() parameter (a list of endpoints to call)
thread = threading.Thread(target=setInterval,args=(callApi,5,['']))
# thread.start() # create a separate thread for api requests asynchronously

# InTheaters
class MoviesView(APIView):
    def get(self, request):
        try : 
            movies_names=["Avatar: The Way of Water","Babylon (I)","Strange World","The Fabelmans", 
                        "The Whale","The Menu","Violent Night","The Banshees of Inisherin",
                        "Black Panther: Wakanda Forever"]
            movies_ids = ["tt1630029", "tt0460714","tt10298840","tt14208870","tt13833688",
                          "tt12003946","tt11813216","tt9114286"]
            movies_set = Movie.objects.filter(title__in=movies_names)
            MoviesSer = MoviesSerializer(movies_set,many=True) 
            return Response(MoviesSer.data,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error" :str(e)}, status=status.HTTP_404_NOT_FOUND)

        
def get_query_set_with_limit(query_set,start, limit): 
    # if limit is specified as a query string , return limited query set, else query set
    if limit and start:
        try: # check if the limit is a valid int
            limit = int(limit)
            start = int(start)
        except ValueError:
            return None
        if limit <= 0 and start<0:
            return None
        return query_set[start:start+limit]
    if limit :
        try :
            limit = int(limit)
        except ValueError:
            return None
        if limit <= 0:
            return None
        return query_set[:limit]
    return query_set

    
def get_todays_date_iso_format():
    return date.today().isoformat()

def filter_movies_by_date_ratings_poster():
    exclude = Q(Q(poster__iendswith="/nopicture.jpg") | Q(ratings__imdb = "N/A"))
    movies = Movie.objects.filter(released__lt=get_todays_date_iso_format())
    movies = movies.exclude(exclude)
    return movies 

def filter_upcoming_movies():
    return (Movie.objects.filter(released__gt = get_todays_date_iso_format()).
           order_by("-released").
           exclude(poster__iendswith="/nopicture.jpg")
    )


def filter_latest_movies(query_set=None):
    if not query_set :
        query_set = Movie.objects.all()
    return (query_set.filter(released__lte= get_todays_date_iso_format()).
           order_by("-released").
           exclude(poster__iendswith="/nopicture.jpg")
    )

# filters trending movies if rating is a string 
def filter_trending_movies_manually():
    # get a list of dictionaries({ratings__imdb:imdb_rating,pk:pk}) of movies released recently
    movies = filter_movies_by_date_ratings_poster()
    movies = movies.values("ratings__imdb","pk")
    for movie in movies :
        # convert the imdb rating to a float (ratings is a json fied initially)
        try :
            movie["ratings__imdb"] = float(movie["ratings__imdb"])
        except:
            movie['ratings__imdb'] = 0
    # make a list of all the movies pk's from the movies dictionary where ratings__imdb >= 7 
    movies_filtered_pks = [movie["pk"] for movie in movies if movie["ratings__imdb"] >= 7]
    # get all the movies by the obtained pks
    return Movie.objects.filter(pk__in = movies_filtered_pks)

def filter_movies_by_date_ratings_poster():
    exclude = Q(Q(poster__iendswith="/nopicture.jpg") | Q(ratings__imdb = "N/A"))
    movies = Movie.objects.filter(released__lt=get_todays_date_iso_format())
    movies = movies.exclude(exclude)
    return movies 

# filters trending movies if rating is a float  
def filter_trending_movies():
    movies = filter_movies_by_date_ratings_poster()
    movies = movies.filter(ratings__imdb__gte = 7)
    return movies

def order_movies_by_imdb():
    movies = filter_movies_by_date_ratings_poster()
    movies = movies.order_by("-ratings__imdb")
    return movies

class TopImdbMoviesView(APIView):
    def get(self,request):
        start = request.query_params.get("start")
        limit =request.query_params.get("limit")
        movies = order_movies_by_imdb()
        movies_limited =get_query_set_with_limit(movies,start=start,limit=limit)
        if movies is None :
            return Response({'error':"invalid limit"},status=status.HTTP_400_BAD_REQUEST)
        
        count = movies_limited.count()
        total_count = movies.count()
        serializer = MoviesSerializer(movies_limited,many=True)
        
        response_dict = {
            "movies" : serializer.data,
            "count":count,
            "total_count":total_count
        }
        
        return Response(response_dict, status=status.HTTP_200_OK)

# MostPopularMovies
class TrendingMoviesView(APIView):
    def get(self, request):
            trending_movies_list = filter_trending_movies()
            # check for limit 
            start = request.query_params.get("start")
            limit =request.query_params.get("limit")
            movies = get_query_set_with_limit(trending_movies_list, start,limit)
            if movies is None :
                    return Response({'error':"invalid limit"},status=status.HTTP_400_BAD_REQUEST)
            
            total_count = trending_movies_list.count()
            count = movies.count()
            serializer = MoviesSerializer(movies,many=True)
            
            response_dict = {
                "movies" : serializer.data,
                "count":count,
                "total_count":total_count
            }
            
            return Response(response_dict,status=status.HTTP_200_OK)
    
class LatestMoviesView(APIView):
    def get(self,request):
            latest_movies_list = filter_latest_movies()
            start = request.query_params.get("start")
            limit =request.query_params.get("limit")
            movies = get_query_set_with_limit(latest_movies_list, start,limit)
            if movies is None :
                return Response({"error":"invalid limit"},status = status.HTTP_400_BAD_REQUEST)
            
            total_count = latest_movies_list.count()
            count = movies.count()
            serializer = MoviesSerializer(movies,many=True)
            
            response_dict = {
                "movies" : serializer.data,
                "count":count,
                "total_count":total_count
            }

            return Response(response_dict,status=status.HTTP_200_OK)

# ComingSoon
class UpcomingMoviesView(APIView):
    def get(self,request):
        # get movies with release date > today
        upcoming_movies_list =filter_upcoming_movies()
        start = request.query_params.get("start")
        limit =request.query_params.get("limit")
        movies = get_query_set_with_limit(upcoming_movies_list, start,limit)
        if movies is None :
            return Response({"error":"invalid limit"},status = status.HTTP_400_BAD_REQUEST)
        
        total_count = upcoming_movies_list.count()
        count = movies.count()
        serializer = MoviesSerializer(movies,many=True)
        
        response_dict = {
            "movies" : serializer.data,
            "count":count,
            "total_count":total_count
        }
        return Response(response_dict,status=status.HTTP_200_OK)

class SimilarMoviesView(APIView):
    def get(self,request,id=None):
        try:
            movie = Movie.objects.get(pk = id)
        except ObjectDoesNotExist:
            return Response({"error":"movie does not exist"},status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error":"invalid id"},status=status.HTTP_400_BAD_REQUEST)
        director = movie.director
        genres = movie.genre.all()
        today = date.today().isoformat()
        similar_movies = Movie.objects.filter(Q(Q(genre__in = genres) | Q(director = director))&Q(released__lt =today)).exclude(pk = movie.pk).distinct()
        similar_movies = similar_movies[:15] if len(similar_movies) > 15 else similar_movies
        movies_serializer = MoviesSerializer(similar_movies, many= True)
        return Response({"movies": movies_serializer.data},status=status.HTTP_200_OK)
    

class FavouritesViewSet(viewsets.ModelViewSet):
    queryset=Favorite.objects.all()
    serializer_class = FavouriteSerializer
    lookup_field=['id','movie_id']
    permission_classes=[IsAuthenticated]

    # get a favorite instance using user's username and movie's id instead of favorite id
    def get_object(self,id,movie_id):
        try: 
            return Favorite.objects.get(user=User.objects.get(pk=id), movie= Movie.objects.get(pk=movie_id))
        except:
            raise Http404()
        
    def list(self,request,pk=None):
        start = request.query_params.get("start",None)
        limit = request.query_params.get("limit",None)
        params = dict(request.query_params)
        user = get_object_or_404(User,pk,{'error':'User does not exist'})
        token_key = request.headers.get('Authorization').split(' ')[1]
        try :
            user_by_token = Token.objects.get(key = token_key).user
        except ObjectDoesNotExist :
            return Response({"error":"User does not exist"},status=status.HTTP_404_NOT_FOUND)
        if user != user_by_token :
            return Response({"error": "Fobidden : You are not allowed to access the favorites of another user."},status = status.HTTP_403_FORBIDDEN)
        
        favourites_list = self.get_queryset().filter(user=User.objects.get(id=pk))
        if not favourites_list.exists():
            return Response({"movies":[],"count":0,'total_count':0},status=status.HTTP_200_OK)
        
        favorite_movies = Movie.objects.filter(favorites__in = favourites_list)
        favorite_movies_filtered =filter_movie_query_set(favorite_movies,params)
        favorite_movies_filtered_limited = get_query_set_with_limit(favorite_movies_filtered,start=start,limit=limit) 

        movies_serializer = MoviesSerializer(favorite_movies_filtered_limited, many=True)
        total_count = favorite_movies_filtered.count()
        count = favorite_movies_filtered_limited.count()

        response_dict = {
            'movies':movies_serializer.data,
            'count':count,
            'total_count':total_count,
        }

        return Response(response_dict,status=status.HTTP_200_OK)
    
    def retrieve(self,request,id,movie_id):
        try:
            self.get_object(id,movie_id) # get the favorite instance  using custom get_object()
            return Response({"found":True}, status=status.HTTP_200_OK) # if found send true
        except Http404:
            return Response({"found":False},status=status.HTTP_404_NOT_FOUND)
            
    def create(self, request): #receives a request containing email and movie_id
        user = User.objects.get(email = request.data["email"])
        movie = Movie.objects.get(pk = request.data["movie_id"])
        try :
            fav = Favorite.objects.get(user= user,movie= movie)# get the favorite instance
            fav.delete() # if found delete it (user removed a movie from his favorites)
            return Response({"deleted/created":"deleted"},status=status.HTTP_200_OK)
        except ObjectDoesNotExist: # if the favorite instance doesn't exist
            fav = Favorite.objects.create(user = user, movie=movie) # create it (user added a movie to his favorites)
            return Response({"deleted/created":"created"},status=status.HTTP_200_OK)

class MoviesCountApiView(APIView):
    def get(self, request):
        category = request.query_params.get('category')
        movies = Movie.objects.all()
        if category is not None: 
            if category =="trending":
                movies = filter_trending_movies()
            elif category == "upcoming":
                movies = filter_upcoming_movies()
            elif category == "latest":
                movies = filter_latest_movies()
            else :
                return Response({"error":"invalid category"}, status = status.HTTP_400_BAD_REQUEST)
        movies_count = movies.count()
        return Response({"movies_count":movies_count},status = status.HTTP_200_OK)


def filter_movie_query_set(query_set, query_params):
        title=  query_params.get('title',None)
        genres = query_params.get('genre',None)
        rated = query_params.get('rated',None)
        released = query_params.get('released',None)
        query = Q()
        if title :
            query.add(Q(title__icontains = title[0]), Q.AND)
        if genres and "All" not in genres :
            try :
                genre= [Genre.objects.get(name=g) for g in genres]
            except ObjectDoesNotExist:
                return Movie.objects.none()
            query.add(Q(genre__in = genre), Q.AND)
        if rated and "All" not in rated :
            query.add(Q(contentRate__iexact = rated[0]) , Q.AND)
        if released and "All" not in released :
            if released[0] == "Unreleased":
                query.add(Q(released__gt=get_todays_date_iso_format()),Q.AND)
            elif released[0] == "older":
                query.add(Q(released__year__lte=2018),Q.AND)
            else:            
                query.add(Q(released__year=int(released[0])) , Q.AND)
        try :
            filtered_query_set = query_set.filter(query).distinct()
        except Exception as e :
            filtered_query_set = Movie.objects.none()
        return filtered_query_set

class MovieListApiView(generics.ListAPIView):
    queryset = Movie.objects.all()
    serializer_class = MoviesSerializer
    def list(self, request):
        if len(self.get_queryset()) == 0 :
            response_dict = {
                        "movies":[],
                        'count':0,
                        'total_count':0}
            return Response(response_dict, status= status.HTTP_404_NOT_FOUND)
        #convert query_params query_dict to a dict
        params = dict(request.query_params)

        # get the start and limit query strings if found else assign it to None
        start = request.query_params.get("start",None)
        limit = request.query_params.get("limit",None)
        
        #movies query set
        movies = self.get_queryset()
        #filter movies according to the available query params
        filtered_movies = filter_movie_query_set(movies, params).order_by('released')

        movies_total_count = filtered_movies.count()

        
        #reduce the number of movies to the limit if available
        filtered_movies = get_query_set_with_limit(filtered_movies, start,limit)

        #if limit is invalid , return an error
        if filtered_movies is None :
            return Response({"error":"invalid limit"}, status=status.HTTP_400_BAD_REQUEST)
        
        movies_count = filtered_movies.count()
        
        # return serialized movies 
        moviesSerializer = MoviesSerializer(filtered_movies,many=True).data

        response_dict = {"movies":moviesSerializer,
                        'count':movies_count,
                        'total_count':movies_total_count}
        
        return Response(response_dict,status=status.HTTP_200_OK)

class MoviesRetrieveApiView(generics.RetrieveAPIView):
    queryset = Movie.objects.all()
    serializer_class = MoviesSerializer
    lookup_field = 'pk'

        
class GenreListApiView(generics.ListAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenresSerializer

class DirecotorListApiView(generics.ListAPIView):
    queryset = Directors.objects.all()
    serializer_class = DirectorsSerializer