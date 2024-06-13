from .models import Movie,Genre, Directors
from django.db.models import Q 
from datetime import date
from abc import ABC, abstractmethod
from django.core.exceptions import ObjectDoesNotExist

def get_todays_date_iso_format():
    return date.today().isoformat()

class Filter(ABC) : 
    @abstractmethod
    def apply_filter(self,queryset) :
        pass
    
class GenreFilter(Filter) : 
    def __init__(self, genres:list, next_handler) :
        self.genres = genres
        self.next_handler = next_handler

    def apply_filter(self,queryset):
        if self.genres and "All" not in self.genres :
            try :
                genres_queryset = [Genre.objects.get(name__iexact=g) for g in self.genres]
            except ObjectDoesNotExist:
                return Movie.objects.none()

            queryset = queryset.filter(genres__in = genres_queryset)

        if self.next_handler : 
            return self.next_handler.apply_filter(queryset)
        
        return queryset

class ReleaseYearFilter(Filter) :
    def __init__(self, release_date:list, next_handler) : 
        self.release_date= release_date
        self.next_handler = next_handler

    def apply_filter(self, queryset):
        today = get_todays_date_iso_format()

        if self.release_date : 
            query = Q()
            for date in self.release_date : 
                if date == "All" :
                    query = Q()
                    break

                if date == "Unreleased":
                    query.add(Q(released__gt = today) , Q.OR)
                
                elif date == "Older" :
                    queryset.filter()
                    query.add(Q(released__year__lte=2014) , Q.OR)
                
                else :
                    queryset.filter()
                    query.add(Q(released__year = date) , Q.OR)

            queryset = queryset.filter(query)
        if self.next_handler : 
            return self.next_handler.apply_filter(queryset)
                
        return queryset
    
class TitleFilter(Filter) :
    def __init__(self, title : list, next_handler) : 
        self.title = title
        self.next_handler = next_handler

    def apply_filter(self, queryset):
        if self.title :
            query = Q()
            for title in self.title:
                if title == "All" :
                    query = Q()
                    break
                query.add(Q(title__icontains=title), Q.OR)
            queryset = queryset.filter(query)

        if self.next_handler : 
            return self.next_handler.apply_filter(queryset)
                
        return queryset
    
class ContentRatingFilter(Filter) :
    def __init__(self, content_rating : list, next_handler) : 
        self.content_rating = content_rating
        self.next_handler = next_handler

    def apply_filter(self, queryset):
        if self.content_rating : 
            query = Q()
            for rating in self.content_rating :
                query.add(Q(content_rating__name__iexact = rating), Q.OR)
            
            queryset = queryset.filter(query)

        if self.next_handler : 
            return self.next_handler.apply_filter(queryset)
                
        return queryset
    

class MovieService : 
    @staticmethod
    def get_all_movies():
        return Movie.objects.all()

    @staticmethod
    def get_upcoming_movies() : 
        today =  get_todays_date_iso_format()
        movies = Movie.objects.filter(released__gte=today).order_by("-released")
        return movies 
    
    @staticmethod
    def get_latest_movies() : 
        today =  get_todays_date_iso_format()
        movies = Movie.objects.filter(released__lte=today).order_by("-released")
        return movies
    
    @staticmethod
    def get_trending_movies() : 
        today =  get_todays_date_iso_format()
        exclude = Q(ratings__imdb = "N/A")
        movies = Movie.objects.filter(released__lt=today).exclude(exclude)
        return movies 
    
    @staticmethod 
    def get_top_imdb_movies() : 
        today =  get_todays_date_iso_format()
        exclude = Q(ratings__imdb = "N/A")
        movies = Movie.objects.filter(released__lt=today).exclude(exclude)
        movies.order_by("-ratings__imdb")
        return movies
    
    @staticmethod
    def get_similar_movies(movie) : 
        director = movie.director
        genres = movie.genres.all()
        today = get_todays_date_iso_format()
        similar_movies = Movie.objects.filter(Q(Q(genres__in = genres) | Q(director = director))&Q(released__lt =today)).exclude(pk = movie.pk).distinct()
        return similar_movies
    
    # def get_recommendations_movies() : 

    @staticmethod
    def filter_movies(queryset, filters : dict):
        title_filter = TitleFilter(filters.get("title"), None)
        genre_filter = GenreFilter(filters.get("genre"),title_filter)
        release_year_filter = ReleaseYearFilter(filters.get("released"), genre_filter)
        content_rating_filter = ContentRatingFilter(filters.get("rated"), release_year_filter)

        return content_rating_filter.apply_filter(queryset).distinct()
    
