from django.db import models
from authentication.models import User

# omdb key : b6661a6a
#multiple movies to one director , but each movie has a sing
class Directors(models.Model):
    name= models.CharField(max_length=256, null=True,unique=True)
    def __str__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=256, unique=True)
    def __str__(self):
        return self.name

class Movie(models.Model) :
    title = models.CharField(max_length=700, blank=False,null=False,unique=True)
    poster = models.URLField(default="https://imdb-api.com/images/128x176/nopicture.jpg")
    ratings = models.JSONField()
    released = models.DateField(max_length=256,null=True)
    genre = models.ManyToManyField(Genre)
    plot = models.TextField()
    contentRate = models.CharField(max_length=256,blank=True,null=True)
    director = models.ForeignKey(Directors, null=True,on_delete=models.SET_NULL,related_name='movies')
    duration = models.IntegerField()
    commentsNumber = models.PositiveIntegerField(default=0)
    image = models.URLField(default="https://imdb-api.com/images/128x176/nopicture.jpg")
    trailer = models.URLField(default="https://imdb-api.com/images/128x176/nopicture.jpg")
    imdbId = models.CharField(max_length=300,null=True,blank=True,unique=True)
    thumbnail = models.URLField(default="https://imdb-api.com/images/128x176/nopicture.jpg")
    def __str__(self):
        return self.title +"("+ str(self.released) +")"
# many favorites can be associated with the same movie (many movies can be set as favorite), nut only one movie can be set as favorite
#a movie can be set as favorite many times and for each favorite instance, only one movie can be set;
# so each favorite instance represents a movie and belongs to a user in the favorites page 
class Favorite(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='favorites',default=1)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE,related_name='favorites')
    def __str__(self):
        return self.movie +" (Favorite)"
    