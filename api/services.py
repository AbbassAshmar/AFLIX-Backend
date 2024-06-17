from .models import Movie,Genre, Favorite, MovieSimilarity
from comments.models import Comment
from django.db.models import Q 
from datetime import date
from abc import ABC, abstractmethod
from django.core.exceptions import ObjectDoesNotExist
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from rest_framework import serializers
from math import floor
from django.db.models.functions import Cast
from django.db.models import Case, When,FloatField, Value
from django.db.models.fields.json import KeyTextTransform

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
    def filter_movies(queryset, filters : dict):
        title_filter = TitleFilter(filters.get("title"), None)
        genre_filter = GenreFilter(filters.get("genre"),title_filter)
        release_year_filter = ReleaseYearFilter(filters.get("released"), genre_filter)
        content_rating_filter = ContentRatingFilter(filters.get("rated"), release_year_filter)
        return content_rating_filter.apply_filter(queryset).distinct()

class RecommenderService :
    @staticmethod
    def get_similar_movies_to_movies(input_movies, count=10) : 
        if count <= 0 or not input_movies:
            return Movie.objects.none()
    
        _cosine_similarity_dataframe = MovieCosineSimilarityService.get_dataframe_of_all_movies()
        input_movies_ids = [movie.pk for movie in input_movies]
        movies_ids = []
        
        count_per_movie = floor(count / len(input_movies_ids)) 
        extras = count_per_movie % len(input_movies_ids)
        
        for movie in input_movies_ids:
            movie_row = _cosine_similarity_dataframe.get(movie,[])
            if len(movie_row) <= 0: 
                continue

            current_count = count_per_movie + (1 if extras > 0 else 0)
            extras -= 1 if extras > 0 else 0

            movie_row = movie_row.sort_values(ascending=False).index.tolist()
            for similar_movie_id  in movie_row:
                if similar_movie_id not in input_movies_ids and similar_movie_id not in movies_ids:
                    movies_ids.append(similar_movie_id)
                    current_count -= 1
                    if current_count == 0:
                        break

        return Movie.objects.filter(pk__in = movies_ids)

    @staticmethod
    def get_similar_movies_to_movie(movie : Movie, count=-1) :
        _cosine_similarity_dataframe = MovieCosineSimilarityService.get_dataframe_of_all_movies()
        movie_row = _cosine_similarity_dataframe.get(movie.pk,[])
            
        if len(movie_row) <= 0 : 
            return Movie.objects.none()
        
        movie_row = movie_row.sort_values(ascending=False)[1:]
        if count > 0 : 
            movie_row = movie_row[0:count+1]

        movies_ids = movie_row.index.tolist()
        return Movie.objects.filter(pk__in = movies_ids)
    
    @staticmethod
    def get_movies_recommendations_for_user(user, count) :
        favorite_movies_movies_ids = Favorite.objects.filter(user = user).values_list('movie', flat=True)
        favorite_movies = Movie.objects.filter(pk__in = favorite_movies_movies_ids)

        commented_on_movies_ids = Comment.objects.filter(user=user).values_list('movie', flat=True)
        commented_on_movies = Movie.objects.filter(pk__in = commented_on_movies_ids)

        movies_list = favorite_movies.union(commented_on_movies)
        movies_list_count = movies_list.count()

        if movies_list_count < count : 
            today =  get_todays_date_iso_format()
            movies = Movie.objects.alias(
                    imdb_rating_text=KeyTextTransform('imdb', 'ratings'),
                    metacritics_rating_text=KeyTextTransform('metacritics', 'ratings')
                ).alias( 
                    combined_ratings=Case(
                        When(
                            ~Q(imdb_rating_text='N/A') & ~Q(imdb_rating_text=None) &
                            ~Q(metacritics_rating_text='N/A') & ~Q(metacritics_rating_text=None),
                            then=Cast('imdb_rating_text', FloatField()) + Cast('metacritics_rating_text', FloatField())
                        ),
                        When(
                            ~Q(imdb_rating_text='N/A') & ~Q(imdb_rating_text=None),
                            then=Cast('imdb_rating_text', FloatField())
                        ),
                        When(
                            ~Q(metacritics_rating_text='N/A') & ~Q(metacritics_rating_text=None),
                            then=Cast('metacritics_rating_text', FloatField())
                        ),
                        default=Value(0),
                        output_field=FloatField()
                    )      
            ).filter(released__lt=today).order_by("-combined_ratings")
            movies_list = movies_list.union(movies[:count - movies_list_count]) 

        recommendations_list = RecommenderService.get_similar_movies_to_movies(movies_list, count)
        return recommendations_list

    
class MovieCosineSimilarityService : 
    class MovieSerializer(serializers.ModelSerializer):
        genres = serializers.SlugRelatedField(many=True,read_only=True,slug_field='name')
        director = serializers.CharField(source='director.name', read_only=True)
        content_rating = serializers.CharField(source='content_rating.name', read_only=True)

        class Meta:
            model = Movie
            fields = ('id','title', 'plot', 'director', 'content_rating', 'genres')

    @staticmethod
    def get_serialized_list_of_movies() : 
        movies= Movie.objects.all()
        return MovieCosineSimilarityService.MovieSerializer(movies, many=True).data
    
    @staticmethod 
    def get_dataframe_of_all_movies() : 
        movies_exist = Movie.objects.exists()

        if movies_exist:
            if not MovieSimilarity.objects.exists():
                MovieCosineSimilarityService.generate_and_store_dataframe_of_all_movies()

        movies_similarities = MovieSimilarity.objects.values("movie_1", "movie_2", "similarity")
        df = pd.DataFrame(list(movies_similarities))
       
        pivot_1 = df.pivot(index='movie_1', columns='movie_2', values='similarity')
        pivot_2 = df.pivot(index='movie_2', columns='movie_1', values='similarity')

        combined_index = pivot_1.index.union(pivot_2.index)
        combined_columns = pivot_1.columns.union(pivot_2.columns)

        pivot_1 = pivot_1.reindex(index=combined_index, columns=combined_columns)
        pivot_2 = pivot_2.T.reindex(index=combined_columns, columns=combined_index).T

        # Combine the DataFrames
        combined = pivot_1.combine_first(pivot_2)
        return combined

    @staticmethod
    def generate_and_store_dataframe_of_all_movies() :
        dataframe = MovieCosineSimilarityService.generate_dataframe_of_all_movies()
        movie_similarity_objects = []

        for i, row in dataframe.iterrows():
            for j, similarity in row.items():
                query = (
                    Q(movie_1__pk=i, movie_2__pk=j) |
                    Q(movie_1__pk=j, movie_2__pk=i)
                )

                if not MovieSimilarity.objects.filter(query).exists() : 
                    movie_similarity_objects.append(MovieSimilarity(
                        movie_1_id=i,
                        movie_2_id=j,
                        similarity=similarity
                    ))

        MovieSimilarity.objects.bulk_create(movie_similarity_objects)
        return True

    @staticmethod
    def generate_and_store_dataframe_row_of_movie(id) : 
        if not Movie.objects.filter(pk=id).exists(): 
            return False 
        
        movies_exist = Movie.objects.all().exclude(pk=id).exists()
        movies_similarities_exist = MovieSimilarity.objects.all().exists()

        if not movies_exist or (movies_exist and not movies_similarities_exist ) : 
            return MovieCosineSimilarityService.generate_and_store_dataframe_of_all_movies()
    
        dataframe = MovieCosineSimilarityService.generate_dataframe_of_all_movies()
        new_movie_row = dataframe.get(id,[])
            
        if len(new_movie_row) <= 0: 
            return False
        
        movie_similarity_objects = []
        for movie, similarity in new_movie_row.items():
            query = (
                Q(movie_1__pk=id, movie_2__pk=movie) |
                Q(movie_1__pk=movie, movie_2__pk=id)
            )

            if not MovieSimilarity.objects.filter(query).exists() : 
                movie_similarity_objects.append(MovieSimilarity(
                    movie_1_id=id,
                    movie_2_id=movie,
                    similarity=similarity
                ))

        MovieSimilarity.objects.bulk_create(movie_similarity_objects)
        return True

    @staticmethod
    def generate_dataframe_of_all_movies():
        all_movies = MovieCosineSimilarityService.get_serialized_list_of_movies()

        movies_dataframe = pd.DataFrame(all_movies)
        movies_dataframe['criteria'] = movies_dataframe.apply(lambda row : f"{' '.join(row['genres'])} {row['director']} {row['title']} {row['plot']}",axis=1)

        tfidf = TfidfVectorizer()
        tfidf_matrix = tfidf.fit_transform(movies_dataframe['criteria'])

        _cosine_similarity_matrix = cosine_similarity(tfidf_matrix)
        _cosine_similarity_dataframe =pd.DataFrame(_cosine_similarity_matrix, index=movies_dataframe['id'], columns=movies_dataframe['id'])

        return _cosine_similarity_dataframe