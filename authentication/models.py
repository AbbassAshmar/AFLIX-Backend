from django.db import models
from django.contrib.auth.models import AbstractUser
# # Create your models here.

class User(AbstractUser):
    email = models.EmailField(unique=True,blank=False)
    username = models.CharField(max_length=256,blank=False,unique=True)
    USERNAME_FIELD = 'email' # the unique identifier in the User model, default is username ..
    REQUIRED_FIELDS = ['username']
    pfp = models.ImageField(upload_to="authentication/imgs/pfps", blank=True,null=True)

    def __str__(self):
        return self.username
    

