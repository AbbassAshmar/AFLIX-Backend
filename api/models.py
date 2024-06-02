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
    
class ContentRating(models.Model): 
    name = models.CharField(max_length=256, unique=True)
    def __str__(self): 
        return self.name

class Movie(models.Model) :
    title = models.CharField(max_length=700, blank=False,null=False,unique=True)
    ratings = models.JSONField()
    released = models.DateField(max_length=256,null=True)
    genre = models.ManyToManyField(Genre)
    plot = models.TextField()
    contentRating = models.ForeignKey(ContentRating,null=True, on_delete=models.SET_NULL,related_name='movies')
    director = models.ForeignKey(Directors, null=True,on_delete=models.SET_NULL,related_name='movies')
    duration = models.CharField(max_length=225)
    trailer = models.URLField(default=None, null=True)
    poster = models.URLField(default="https://imdb-api.com/images/128x176/nopicture.jpg",null=True)
    image = models.URLField(default=None, null=True)
    thumbnail = models.URLField(default="https://imdb-api.com/images/128x176/nopicture.jpg", null=True)
    imdbId = models.CharField(max_length=300,null=True,blank=True,unique=True)
    
    @property
    def comments_replies_count(self):
        comments_count = self.comments.count()
        replies_count = self.replies.count()
        return comments_count + replies_count
    
    def __str__(self):
        return self.title 
    

class Favorite(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='favorites',default=1)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE,related_name='favorites')
    def __str__(self):
        return self.user.username + " : " +self.movie.title 
    