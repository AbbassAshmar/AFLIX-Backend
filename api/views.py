from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .models import *
from rest_framework.authtoken.models import Token
from django.core.exceptions import ObjectDoesNotExist
from datetime import date
import threading
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q 
from helpers.response import successResponse, failedResponse
from helpers.get_object_or_404 import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound

# event = threading.Event() # Create an Event to control the timimg of the thread
# def setInterval(func,time,name):
#     while True :
#         for n in name :
#             func(n) # call the function responsible for calling an api at one of the endpoints
#             event.wait(time) # wait for event.set(), if given wait for it then run the function
        
# asign a function to thread, and specify the arguments in args=() parameter (a list of endpoints to call)

# thread = threading.Thread(target=setInterval,args=(callApi,5,['']))
# thread.start() # create a separate thread for api requests asynchronously


# metadata : 
#     'count'=>$countAfterPagination,
#     'total_count'=>$total_count,
#     'pages_count' => $pages_count,
#     'current_page'=>$page,
#     'limit'=>$limit, 

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


# filters trending movies if rating is a float  
def filter_trending_movies():
    movies = filter_movies_by_date_ratings_poster()
    return movies

def order_movies_by_imdb():
    movies = filter_movies_by_date_ratings_poster()
    movies = movies.order_by("-ratings__imdb")
    return movies

class MoviePagination(PageNumberPagination):
    page_size = 30  # Default page size
    page_size_query_param = 'limit'
    max_page_size = 200  # Maximum page size

    def paginate_queryset_with_details(self,filtered_movies, request):
        paginated_queryset = self.paginate_queryset(filtered_movies, request)
        return {
            "result" : paginated_queryset,
            "details" : {
                'count': len(paginated_queryset),
                'total_count':self.page.paginator.count,
                'pages_count':self.page.paginator.num_pages,
                'current_page': self.page.number,
                'limit': self.get_page_size(request),
            }
        }

class MovieListApiView(generics.ListAPIView):
    pagination_class = MoviePagination
    queryset = Movie.objects.all()
    serializer_class = MoviesSerializer

    def list(self, request):
        params = dict(request.query_params)

        movies = self.get_queryset()
        filtered_movies = filter_movie_query_set(movies, params).order_by('released')

        paginator = self.pagination_class()
        paginated_filter_movies = paginator.paginate_queryset_with_details(filtered_movies, request)

        moviesSerializer = MoviesSerializer(paginated_filter_movies['result'],many=True)
        data = {"movies":moviesSerializer.data}
        metadata = paginated_filter_movies['details']
        
        response = successResponse(data, metadata)
        return Response(response,status=status.HTTP_200_OK)
       

class TopImdbMoviesView(generics.ListAPIView):
    pagination_class = MoviePagination
    serializer_class = MoviesSerializer

    def list(self, request):
        movies = order_movies_by_imdb()

        paginator = self.pagination_class()
        paginated_movies = paginator.paginate_queryset_with_details(movies, request)
        
        moviesSerializer = self.serializer_class(paginated_movies['result'],many=True,context={"request":request})

        data = {"movies":moviesSerializer.data}
        metadata = paginated_movies['details']
        
        response = successResponse(data, metadata)
        return Response(response,status=status.HTTP_200_OK)


class TrendingMoviesView(generics.ListAPIView):
    pagination_class = MoviePagination
    serializer_class = MoviesSerializer

    def list(self, request):
            movies = filter_trending_movies()

            paginator = self.pagination_class()
            paginated_movies = paginator.paginate_queryset_with_details(movies, request)
            moviesSerializer = self.serializer_class(paginated_movies['result'],many=True,context={"request":request})
            
            data = {"movies":moviesSerializer.data}
            metadata = paginated_movies['details']
            
            response = successResponse(data, metadata)
            return Response(response,status=status.HTTP_200_OK)
    

class LatestMoviesView(generics.ListAPIView):
    pagination_class = MoviePagination
    serializer_class = MoviesSerializer
   
    def get(self,request):
        movies = filter_latest_movies()
        
        paginator = self.pagination_class()
        paginated_movies = paginator.paginate_queryset_with_details(movies, request)
        moviesSerializer = self.serializer_class(paginated_movies['result'],many=True)
        
        data = {"movies":moviesSerializer.data}
        metadata = paginated_movies['details']
        
        response = successResponse(data, metadata)
        return Response(response,status=status.HTTP_200_OK)


class UpcomingMoviesView(APIView):
    pagination_class = MoviePagination
    serializer_class = MoviesSerializer

    def get(self,request):
        movies =filter_upcoming_movies()

        paginator = self.pagination_class()
        paginated_movies = paginator.paginate_queryset_with_details(movies, request)
        moviesSerializer = self.serializer_class(paginated_movies['result'],many=True,context={"request":request})
        
        data = {"movies":moviesSerializer.data}
        metadata = paginated_movies['details']
        
        response = successResponse(data, metadata)
        return Response(response,status=status.HTTP_200_OK)
        

class SimilarMoviesView(APIView):
    pagination_class = MoviePagination
    serializer_class = MoviesSerializer

    def get(self,request,id=None):
        movie = get_object_or_404(Movie, id, "Movie does not exist.")

        director = movie.director
        genres = movie.genres.all()

        today = date.today().isoformat()
        similar_movies = Movie.objects.filter(Q(Q(genres__in = genres) | Q(director = director))&Q(released__lt =today)).exclude(pk = movie.pk).distinct()
        
        paginator = self.pagination_class()
        paginated_movies = paginator.paginate_queryset_with_details(similar_movies, request)
        moviesSerializer = self.serializer_class(paginated_movies['result'],many=True,context={"request":request})
        
        data = {"movies":moviesSerializer.data}
        metadata = paginated_movies['details']
        
        response = successResponse(data, metadata)
        return Response(response,status=status.HTTP_200_OK)
    
    
class FavoritesAPIView(generics.ListCreateAPIView):
    queryset=Favorite.objects.all()
    pagination_class = MoviePagination
    permission_classes=[IsAuthenticated]
    serializer_class = MoviesSerializer
        
    def get(self,request):
        user = request.user
        params = dict(request.query_params)

        favorite_movies = self.get_queryset().filter(user=user.pk).values_list('movie', flat=True)
        movies = Movie.objects.filter(id__in=favorite_movies)
        filtered_movies =filter_movie_query_set(movies,params)

        paginator = self.pagination_class()
        paginated_movies = paginator.paginate_queryset_with_details(filtered_movies, request)
        moviesSerializer = self.serializer_class(paginated_movies['result'],many=True)
        
        data = {"movies":moviesSerializer.data}
        metadata = paginated_movies['details']
        
        response = successResponse(data, metadata)
        return Response(response,status=status.HTTP_200_OK)
            
    def create(self, request): #receives a request containing email and movie_id
        user = request.user
        movie = get_object_or_404(Movie, request.data["movie_id"], "Movie does not exist.")

        try :
            fav = Favorite.objects.get(user= user,movie= movie)
            fav.delete() 
            response = successResponse({"action":"deleted"},None)
            return Response(response,status=status.HTTP_200_OK)
        
        except ObjectDoesNotExist: 
            Favorite.objects.create(user=user, movie=movie) 
            response = successResponse({"action":"created"},None)
            return Response(response,status=status.HTTP_201_CREATED)

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

        print(genres)
        query = Q()
        if title :
            query.add(Q(title__icontains = title[0]), Q.AND)

        if genres and "All" not in genres :
            try :
                genre= [Genre.objects.get(name__iexact=g) for g in genres]
            except ObjectDoesNotExist:
                return Movie.objects.none()

            query.add(Q(genres__in = genre), Q.AND)

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

class MoviesRetrieveApiView(generics.RetrieveAPIView):
    queryset = Movie.objects.all()
    serializer_class = MoviesSerializer
    lookup_field = 'pk' 

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context      

class GenreListApiView(generics.ListAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenresSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        genres_count = Genre.objects.count()
        response = successResponse({'genres':serializer.data},{'count':genres_count})

        return Response(response, status=status.HTTP_200_OK)

class DirecotorListApiView(generics.ListAPIView):
    queryset = Directors.objects.all()
    serializer_class = DirectorsSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        directors_count = Directors.objects.count()
        response = successResponse({'directors':serializer.data},{'count':directors_count})

        return Response(response, status=status.HTTP_200_OK)

class ContentRatingListApiView(generics.ListAPIView):
    queryset = ContentRating.objects.all()
    serializer_class = ContentRatingSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        content_ratings_count = ContentRating.objects.count()
        response = successResponse({'content_ratings':serializer.data},{'count':content_ratings_count})

        return Response(response, status=status.HTTP_200_OK)