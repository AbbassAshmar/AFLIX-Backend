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
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .services import MovieService,RecommenderService

# event = threading.Event() # Create an Event to control the timimg of the thread
# def setInterval(func,time,name):
#     while True :
#         for n in name :
#             func(n) # call the function responsible for calling an api at one of the endpoints
#             event.wait(time) # wait for event.set(), if given wait for it then run the function
        
# asign a function to thread, and specify the arguments in args=() parameter (a list of endpoints to call)

# thread = threading.Thread(target=setInterval,args=(callApi,5,['']))
# thread.start() # create a separate thread for api requests asynchronously


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
        filters = dict(request.query_params)

        movies = MovieService.get_all_movies()
        filtered_movies = MovieService.filter_movies(movies, filters)

        paginator = self.pagination_class()
        paginated_filter_movies = paginator.paginate_queryset_with_details(filtered_movies, request)

        moviesSerializer = self.serializer_class(paginated_filter_movies['result'],many=True,context={"request":request})
        data = {"movies":moviesSerializer.data}
        metadata = paginated_filter_movies['details']
        
        response = successResponse(data, metadata)
        return Response(response,status=status.HTTP_200_OK)
       

class TopImdbMoviesView(generics.ListAPIView):
    pagination_class = MoviePagination
    serializer_class = MoviesSerializer

    def list(self, request):
        movies = MovieService.get_top_imdb_movies()

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
            movies = MovieService.get_trending_movies()

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
   
    def list(self,request):
        movies = MovieService.get_latest_movies()

        paginator = self.pagination_class()
        paginated_movies = paginator.paginate_queryset_with_details(movies, request)
        moviesSerializer = self.serializer_class(paginated_movies['result'],many=True,context={'request' : request})
        
        data = {"movies":moviesSerializer.data}
        metadata = paginated_movies['details']
        
        response = successResponse(data, metadata)
        return Response(response,status=status.HTTP_200_OK)


class UpcomingMoviesView(generics.RetrieveAPIView):
    pagination_class = MoviePagination
    serializer_class = MoviesSerializer

    def retrieve(self,request):
        movies = MovieService.get_upcoming_movies()

        paginator = self.pagination_class()
        paginated_movies = paginator.paginate_queryset_with_details(movies, request)
        moviesSerializer = self.serializer_class(paginated_movies['result'],many=True,context={"request":request})
        
        data = {"movies":moviesSerializer.data}
        metadata = paginated_movies['details']
        
        response = successResponse(data, metadata)
        return Response(response,status=status.HTTP_200_OK)
        

class SimilarMoviesView(generics.ListAPIView):
    pagination_class = MoviePagination
    serializer_class = MoviesSerializer

    def list(self,request,id=None):
        movie = get_object_or_404(Movie, id, "Movie does not exist.")
        similar_movies = RecommenderService.get_similar_movies_to_movie(movie)

        paginator = self.pagination_class()
        paginated_movies = paginator.paginate_queryset_with_details(similar_movies, request)
        moviesSerializer = self.serializer_class(paginated_movies['result'],many=True,context={"request":request})
        
        data = {"movies":moviesSerializer.data}
        metadata = paginated_movies['details']
        
        response = successResponse(data, metadata)
        return Response(response,status=status.HTTP_200_OK)
    
class RecommendationsApiView(generics.ListAPIView) : 
    permission_classes = [IsAuthenticated]
    serializer_class = MoviesSerializer

    def list(self, request) : 
        user = request.user
        movies = RecommenderService.get_movies_recommendations_for_user(user, 10) 

        moviesSerializer = self.get_serializer(movies ,many=True, context={"request" : request})
        data = {"movies":moviesSerializer.data}
        
        response = successResponse(data, None)
        return Response(response,status=status.HTTP_200_OK)

class FavoritesAPIView(generics.ListCreateAPIView):
    queryset=Favorite.objects.all()
    pagination_class = MoviePagination
    permission_classes=[IsAuthenticated]
    serializer_class = MoviesSerializer
        
    def list(self,request):
        user = request.user
        filters = dict(request.query_params)

        favorite_movies = self.get_queryset().filter(user=user.pk).values_list('movie', flat=True)
        movies = Movie.objects.filter(id__in=favorite_movies)
        filtered_movies = MovieService.filter_movies(movies, filters)

        paginator = self.pagination_class()
        paginated_movies = paginator.paginate_queryset_with_details(filtered_movies, request)
        moviesSerializer = self.get_serializer(paginated_movies['result'],many=True)
        
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
        movies = Movie.objects.all()
        return Response(successResponse({'movies_count' : movies.count()}),status = status.HTTP_200_OK)

class IgnoreInvalidToken(TokenAuthentication):
    def authenticate_credentials(self, key):
        try:
            return super().authenticate_credentials(key)
        except AuthenticationFailed:
            return None
        
class MoviesRetrieveApiView(generics.RetrieveAPIView):
    queryset = Movie.objects.all()
    serializer_class = MoviesSerializer
    authentication_classes = [IgnoreInvalidToken]
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