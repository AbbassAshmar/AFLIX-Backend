from django.urls import path,include
from rest_framework.routers import SimpleRouter, DynamicRoute, Route
from .views import *

# class customRouter(SimpleRouter):
#     routes= [
#         Route(
#             url=r'^{prefix}$',
#             mapping = {'post':'create'},
#             name= '{basename}-create',
#             detail = False,
#             initkwargs={}
#         ),
#         Route(
#             url=r'^{prefix}/(?P<id>[^/]+)/(?P<movie_id>[^/]+)$',
#             mapping ={'get':'retrieve'},
#             name='{basename}-detail',
#             detail=True,
#             initkwargs={}
#         ),
#         Route(
#             url=r'^{prefix}/(?P<pk>[^/]+)',
#             mapping={'get':'list'},
#             name='{basename}-list',
#             detail=False,
#             initkwargs={}
#         )
#     ]

# router = customRouter()
# router.register('movies/favorites',FavouritesViewSet,basename="fav")

urlpatterns =[
    path("users/user/favorites/", FavoritesAPIView.as_view(), name="favorites"),
    path("movies/trending/", TrendingMoviesView.as_view(), name="movie-trending"),
    path("movies/latest/", LatestMoviesView.as_view(), name="movie-latest"),
    path("movies/upcoming/", UpcomingMoviesView.as_view(), name="movie-upcoming"),
    path("movies/count/", MoviesCountApiView.as_view(), name="movies-count"),
    path("movies/", MovieListApiView.as_view(),name="movie-list"),
    path("genres/", GenreListApiView.as_view(), name="genre-list"),
    path("content-ratings/", ContentRatingListApiView.as_view(), name="content-rating-list"),
    path("directors/",DirecotorListApiView.as_view(),name="director-list"),
    path("movies/<int:id>/similar/", SimilarMoviesView.as_view(), name="movie-similar"),
    path("movies/top-imdb/", TopImdbMoviesView.as_view(), name="movie-top-imdb"),
    path("movies/<int:pk>/", MoviesRetrieveApiView.as_view(), name="movie-details"),
]
