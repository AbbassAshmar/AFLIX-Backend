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
from rest_framework.pagination import PageNumberPagination
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .services import MovieService,RecommenderService



class IgnoreInvalidToken(TokenAuthentication):
    def authenticate_credentials(self, key):
        try:
            return super().authenticate_credentials(key)
        except AuthenticationFailed:
            return None  

class MoviePagination(PageNumberPagination):
    page_size = 30  # Default page size
    page_size_query_param = 'limit'
    max_page_size = 200  # Maximum page size

    def paginate_queryset_with_details(self,filtered_movies, request):
        if not filtered_movies : 
           return {
                "result" : [],
                "details" : {
                    'count':0,
                    'total_count':0,
                    'pages_count':0,
                    'current_page': 0,
                    'limit': 0,
                }
            } 
      
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
    

class MoviesRetrieveApiView(generics.RetrieveAPIView):
    serializer_class = MoviesSerializer
    authentication_classes = [IgnoreInvalidToken]
    lookup_field = 'pk' 
    
    def retrieve(self, request, pk = None):
        movie = MovieService.get_by_id(pk)
        serializer = self.get_serializer(movie,context={"request" : request})

        data = {"movie":serializer.data}
        payload = successResponse(data,None)

        return Response(payload, status.HTTP_200_OK)


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

class SliderMoviesApiView(generics.ListAPIView) : 
    pagination_class = MoviePagination
    serializer_class = MoviesSerializer

    def list(self, request):
        movies = MovieService.get_trending_movies()
        movies = MovieService.only_movies_with_images(movies)
        
        paginator = self.pagination_class()
        paginated_movies = paginator.paginate_queryset_with_details(movies, request)
        movies_serializer = self.get_serializer(paginated_movies['result'],many=True,context={"request":request})
        
        data = {"movies":movies_serializer.data}
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
        movie = MovieService.get_by_id(id)
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
    pagination_class = MoviePagination

    def list(self, request) : 
        user = request.user
        movies = RecommenderService.get_movies_recommendations_for_user(user, -1) 
        
        paginator = self.pagination_class()
        paginated_movies = paginator.paginate_queryset_with_details(movies, request)
        moviesSerializer = self.get_serializer(paginated_movies['result'] ,many=True, context={"request" : request})

        data = {"movies":moviesSerializer.data}
        metadata = paginated_movies['details']
        
        response = successResponse(data, metadata)
        return Response(response,status=status.HTTP_200_OK)

class FavoritesAPIView(generics.ListCreateAPIView):
    queryset=Favorite.objects.all()
    pagination_class = MoviePagination
    permission_classes=[IsAuthenticated]
    serializer_class = MoviesSerializer
        
    def list(self,request):
        user = request.user
        filters = dict(request.query_params)

        movies = MovieService.get_favorites_movies(user)
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
        movie = MovieService.get_by_id(request.data["movie_id"])

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
        movies = MovieService.get_all_movies()
        response = successResponse({'movies_count' : movies.count()},None)
        return Response(response,status = status.HTTP_200_OK)

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