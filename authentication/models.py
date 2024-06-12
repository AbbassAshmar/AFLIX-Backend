from django.db import models
from django.contrib.auth.models import AbstractUser
from rest_framework.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
import re 

class User(AbstractUser):
    email = models.EmailField(unique=True,blank=False)
    username = models.CharField(max_length=256,blank=False,unique=False)
    USERNAME_FIELD = 'email' # the unique identifier in the User model, default is username ..
    REQUIRED_FIELDS = ['username']
    pfp = models.ImageField(upload_to="authentication/imgs/pfps", blank=True,null=True)

    def __str__(self):
        return self.username
    
    def set_password(self, raw_password,password_field="password"):
        self.validate_password(raw_password ,password_field)
        super().set_password(raw_password)

    def clean(self):
        self.validate_email(self.email)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
    
    def validate_email(self, email):
        user = User.objects.filter(email = email).first()

        if user and not user == self  :
            raise ValidationError({"email" : "This email has already been used."})
        
        if not bool(re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email)):
            raise ValidationError({"email" : "Invalid email format."})
    
        return None
    
    @staticmethod
    def validate_passwords_match(password, confirm_password, password_field='password', confirm_password_field='confirm_password'):
        if not password == confirm_password:
            raise ValidationError({password_field: "", confirm_password_field: "Passwords do not match."})
    

    def validate_password(self, password:str, password_field="password") :
        if len(password) < 8 : 
            raise ValidationError({password_field : "Password has to be atleast 8 characters long."})
        
        if not bool(re.match(r'^(?=.*[a-zA-Z])(?=.*[0-9])', password)):
            raise ValidationError({password_field : 'Password must consist of both characters and digits.'})

    @staticmethod
    def validate_register_required_fields(fields : dict):
        required_fields = ['password', 'email' , 'username' , 'confirm_password']
        missing_fields = {field : f"{field.replace('_', ' ')} is Required" for field in required_fields if not fields.get(field, "")}

        if missing_fields : 
            raise ValidationError(missing_fields)
        
    @staticmethod
    def validate_login_required_fields(fields : dict):
        required_fields = ['email' , 'password']
        missing_fields = {field : f"{field.replace('_', ' ')} is Required" for field in required_fields if not fields.get(field, "")}

        if missing_fields : 
            raise ValidationError(missing_fields)
        
    def check_password_belongs_to_user(self, password, password_field="password") : 
        if not check_password(password, self.password) :
            raise ValidationError({password_field : "Wrong password."})

        
    

