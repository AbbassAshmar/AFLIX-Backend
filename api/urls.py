from django.urls import path,include
from rest_framework.routers import SimpleRouter, DynamicRoute, Route
from .views import *

class customRouter(SimpleRouter):
    routes= [
        Route(
            url=r'^{prefix}$',
            mapping = {'post':'create'},
            name= '{basename}-create',
            detail = False,
            initkwargs={}
        ),
        Route(
            url=r'^{prefix}/(?P<username>[^/]+)/(?P<movie_id>[^/]+)$',
            mapping ={'get':'retrieve'},
            name='{basename}-detail',
            detail=True,
            initkwargs={}
        ),
    ]
router = customRouter()
router.register('favourite',FavouritesViewSet,basename="fav")

urlpatterns =[
    path("",include(router.urls)),
    path("", MoviesView.as_view(), name="index"),

    path("movies/trending/", TrendingMoviesView.as_view(), name="trendingMoives"),
    path("movies/latest/", LatestMoviesView.as_view(), name="latestMovies"),
    path("movies/upcoming/", UpcomingMoviesView.as_view(), name="upcomingMovies"),

    path("movies/", MovieListApiView.as_view(),name="movie-list"),
    path("genrecollection/", allGenres.as_view(), name="genreCollection"),
    path("directorcollection/",allDirectors.as_view(),name="directorCollection"),
    path("similarmovies/", SimilarMoviesView.as_view(), name="similarMovies"),
    path("moviebycategory/",Category_Id_Movies_Apiview.as_view(),name="moviebycategory")
]
