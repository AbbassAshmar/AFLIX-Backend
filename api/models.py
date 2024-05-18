from django.db import models
from authentication.models import User

class PageInfo(models.Model):
    endpoint = models.CharField(max_length=250, unique=True)
    page = models.IntegerField(default=1)
    def __str__(self):
        return self.endpoint + " : " + str(self.page)

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
    ratings = models.JSONField()
    released = models.DateField(max_length=256,null=True)
    genre = models.ManyToManyField(Genre)
    plot = models.TextField()
    contentRate = models.CharField(max_length=256,blank=True,null=True)
    director = models.ForeignKey(Directors, null=True,on_delete=models.SET_NULL,related_name='movies')
    duration = models.CharField(max_length=225)
    trailer = models.URLField(default=None, null=True)
    poster = models.URLField(default="https://imdb-api.com/images/128x176/nopicture.jpg",null=True)
    image = models.URLField(default="https://imdb-api.com/images/128x176/nopicture.jpg", null=True)
    thumbnail = models.URLField(default="https://imdb-api.com/images/128x176/nopicture.jpg", null=True)
    imdbId = models.CharField(max_length=300,null=True,blank=True,unique=True)
    
    def __str__(self):
        return self.title 
# many favorites can be associated with the same movie (many movies can be set as favorite), nut only one movie can be set as favorite
#a movie can be set as favorite many times and for each favorite instance, only one movie can be set;
# so each favorite instance represents a movie and belongs to a user in the favorites page 
class Favorite(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='favorites',default=1)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE,related_name='favorites')
    def __str__(self):
        return self.user.username + " : " +self.movie.title 
    