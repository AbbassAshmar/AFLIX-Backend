from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
# # Create your models here.

class User(AbstractUser):
    email = models.EmailField(unique=True,blank=False)
    username = models.CharField(max_length=256,blank=False,unique=True)
    USERNAME_FIELD = 'email' # the unique identifier in the User model, default is username ..
    REQUIRED_FIELDS = ['username']
    pfp = models.ImageField(upload_to="authentication/imgs/pfps", blank=True,null=True)

    def __str__(self):
        return self.username
#unlike in Multi-table inheritance method, in abstract inheritace the parent class is not created in the db.
# in Multi-table inheritance , there is not abstract True , just inherit.NOT preferable bacause of extra JOINS
class Base(models.Model): # abstract model for abstract inheritance, this model with abstract True is not created in the db
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    text = models.TextField(blank=False,editable=True)
    date = models.DateTimeField(editable=True,default=timezone.now,blank=True)
    def __str__(self):
        return self.user.username + ":" + self.text

    class Meta:
        abstract = True

class Comments(Base): # inherits all the fields from abstract Base model , with additional fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="Comments",null=False)
    profile = models.ForeignKey(User,on_delete=models.SET_NULL,related_name="comment_profile",null=True,blank=True)
    movie_page = models.ForeignKey("api.Movie",on_delete=models.CASCADE,null=False,default=1)
    user_ld = models.ManyToManyField(User, through="CommentsLikesDislike")

class Replies(Base):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="Replies",null=False)
    parent_comment = models.ForeignKey(Comments, on_delete=models.CASCADE,related_name="replies",null=False)
    user_replying_to = models.ForeignKey(User,on_delete=models.CASCADE,related_name="replied_to",null=False,default=1)
    profile = models.ForeignKey(User,on_delete=models.SET_NULL,related_name="reply_profile",blank=True,null=True)
    movie_page = models.ForeignKey("api.Movie",on_delete=models.CASCADE,null=False,default=1)
    user_ld = models.ManyToManyField(User, through="RepliesLikesDislike")


class CommentsLikesDislike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comments, on_delete=models.CASCADE)
    liked = models.BooleanField(default= False)
    disliked = models.BooleanField(default= False)

class RepliesLikesDislike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reply = models.ForeignKey(Replies, on_delete=models.CASCADE)
    liked = models.BooleanField(default= False) # Liked is a detector if the user liked a specific comment or reply
    disliked = models.BooleanField(default= False)

# create a custom ManyToMany table (add to it, beside the user column and comments column, a liked and disliked columns)
# to do this , add the manyToManyField normally, but use through ="ModelName", where modelName is the table of relation.

