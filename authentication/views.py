from rest_framework.response import Response
from rest_framework import viewsets,status
from django.views.decorators.csrf import csrf_exempt
from .models import *
from .serializers import *
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import check_password
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.core.exceptions import ObjectDoesNotExist
from helpers.get_object_or_404 import get_object_or_404
import random 
import string
import re
import requests


def remove_tuples_from_list(arr, *args):
    for key in args :
        for item in arr :
            if item[0] == key:
                arr.remove(item)
    return arr
    
def contains_letters_and_numbers(string):
    return bool(re.search(r'^(?=.*[a-zA-Z])(?=.*[0-9])', string))

def validate_password(password , confirm_password=None):
    if len(password) < 8 :
        return {"error":"Your password must be at least 8 characters !"}
    if not contains_letters_and_numbers(password):
        return {"error":"Password must contain numbers and characters !"}
    if not password == confirm_password and confirm_password!=None:
        return {"error":"Passwords do not match !"}
    return None

class UserViewSet(viewsets.ViewSet):
    lookup_field = 'pk' # overrides the default field to look for in retrieve, the default is pk 
    serializer_class = UserSerializer

    # apply isAuthenticated permission check to partial_update method only
    def get_permissions(self):
        if self.request.method == "PATCH":
            # permission list is used by check_permissions() method 
            return [IsAuthenticated()]
        # return [permission() for permission in permission_classes]
        return super().get_permissions()
    
    def list(self, request):
        queryset = User.objects.all()
        serializer = self.serializer_class(queryset, many =True)
        return Response(serializer.data)

    def create(self ,request):
        new_user = request.data

        if User.objects.filter(email = new_user['email']).exists():
            return Response({"error":"Email already used"}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username = new_user['username']).exists():
            while {'username':new_user['username']} in User.objects.values('username'):
                usernamee = new_user['username']+ " #"+str(random.randrange(1000,99999))
                new_user['username'] =usernamee

        password =  new_user["password"]
        confirm_pass =new_user["confirmPass"]

        validatePass=validate_password(password,confirm_pass) 
        if validatePass is not None:
            return Response(validatePass,status=status.HTTP_400_BAD_REQUEST)
        
        user =User.objects.create_user(username = new_user["username"], email=new_user["email"], password = new_user["password"],pfp=None)
        token = Token.objects.create(user = user)

        response = {
            "metadata" : None,
            "success" : True,
            "error" : None,
            "data" : {
                "user" : self.serializer_class(user).data,
                "token" :  token.key
            }
        }

        return Response(response, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        try :
            user = User.objects.get(pk = pk)
            serializer = self.serializer_class(user)

            response = {
                "metadata" : None,
                "success" : True,
                "error" : None,
                "data" : {
                    "user" : serializer.data
                }
            }
            
            return Response(response, status=status.HTTP_200_OK)
        except :
            response = {
                "metadata" : None,
                "success" : True,
                "error" : {"message" : "User not Found", "code" : 404},
                "data" :None,
            }
            return Response(response, status= status.HTTP_404_NOT_FOUND)
        
    def partial_update(self, request , pk=None):
        # get the user that sent the request
        requester_user = Token.objects.get(key = request.headers["Authorization"].split(" ")[1]).user
        # get the user who's information to be updated
        user = get_object_or_404(User,pk,"user does not exist")
        # check if both if the user who sent the request has the info to be updated
        if not (requester_user == user):
            return Response({"error": "not authorized"}, status=status.HTTP_403_FORBIDDEN)
        # remove empty info from the request's body
        user_info = {i:request.data[i] for i in request.data if not (len(request.data[i]) == 0)}

        # if password is in requests body , update it alone
        if "newPassword" in user_info and user_info["newPassword"] :
            new_pass = user_info["newPassword"] 
            confirm_pass = user_info["confirmPassword"]
            # check if old password is correct
            if not check_password(user_info['oldPassword'],user.password):
                return Response({"error":"old password is not correct"},status=status.HTTP_400_BAD_REQUEST)
            validatePass=validate_password(new_pass,confirm_pass) 
            if validatePass is not None:
                return Response(validatePass,status=status.HTTP_400_BAD_REQUEST)
            # update the password of the user
            user.set_password(new_pass)
            # update the password of the instance in the database
            user.save(update_fields=["password"])

        # check if the new email is in the info to be updated
        if "email" in user_info :
            try:
                #get the user of the email to be updated
                user_by_email = User.objects.get(email = user_info["email"])
                #if email is the same as the original , remove it from the info to be updated
                if user == user_by_email :
                    user_info.pop("email")
                #if the client is updating his email to an email that belongs to another user, send an error response
                else :
                    return Response({"error":"email already used"}, status = status.HTTP_400_BAD_REQUEST)
            # if the email is not used and different from the original , continue 
            except ObjectDoesNotExist:
                pass
        
        # create a new array of user's info without the passwords (already updated)
        cleaned_array = remove_tuples_from_list(list(user_info.items()),"newPassword","oldPassword","confirmPassword","pfp") 
        # the message to be sent in the response ,(contains updated info)
        response_message = {}
        # save the propfile picture if found using model.ImageField.save(name,image)   
        if 'pfp' in user_info and user_info['pfp']:
            user.pfp.save('pfp.jpg',user_info["pfp"])   
            response_message["pfp"] = "http://127.0.0.1:8000"+user.pfp.url
        # update the fields of the user model by the cleaned array (password already updated)
        # equivalent to : user.email = email , user.username = username ...
        for info, value in cleaned_array:
            setattr(user, info, value)
            response_message[info] = value
        # update the row in the db (only update changed fields)
        user.save(update_fields=[i[0] for i in cleaned_array])
        return Response(response_message, status=status.HTTP_200_OK)  
                                             
    def delete(self,request, pk=None):
        pass


class googleLoginViewSet(viewsets.ViewSet):
    def create(self, request):
        email= request.data["email"]
        try :
            user = User.objects.get(email = email)
        except ObjectDoesNotExist:
            return Response({"error": "Wrong email or password 1 !"}, status= status.HTTP_404_NOT_FOUND)
        token = Token.objects.get_or_create(user=user)[0]
        return Response({"user" :UserSerializer(user).data, "token" : token.key},status=status.HTTP_302_FOUND)


class LoginViewSet(viewsets.ViewSet):
    def create(self , request):
        email = request.data["email"]
        password = request.data["password"]

        response = {
            "metadata" : None,
            "success" : True,
            "error" : None,
            "data" : None, 
        }

        try :
            user = User.objects.get(email = email)
        except ObjectDoesNotExist:
            response["success"] = False
            response["metadata"] = {"error_fields" : ["email"]}
            response["error"] = {
                "code": 404 , 
                "message":"Validation Error.",
                "details" : {"password" : "Account with this email does not exist!"}
            }

            return Response(response, status= status.HTTP_404_NOT_FOUND)
        
        if not check_password(password, user.password) :
            response["success"] = False
            response["metadata"] = {"error_fields" : ["email","password"]}
            response["error"] = {
                "code": 404 , 
                "message":"Validation Error.",
                "details" : {"password" : "Wrong Email or Password"}
            }
            
            return Response(response, status= status.HTTP_404_NOT_FOUND)
        
        response = {
            "metadata" : None,
            "success" : True,
            "error" : None,
            "data" : {
                "user" : UserSerializer(user).data,
                'token' : Token.objects.get_or_create(user = user)[0].key
            }
        }
        
        return Response(response,status=status.HTTP_200_OK)

class LogoutViewSet(viewsets.ViewSet):
    permission_classes =[IsAuthenticated]
    def create(self, request):
        request.user.auth_token.delete()
        return Response({"error":"user logged out"})

class TokenValidate(APIView):
    def get(self, request, *args, **kwargs):
        client_id = "798671795051-c95amd54jght2rvvkbnqog71ilut2kch.apps.googleusercontent.com"
        access_token = request.headers.get("Authorization",None)

        if access_token is None :
            return Response({"error" :"Access token missing"}, status=status.HTTP_403_FORBIDDEN)
        
        access_token = access_token.split(" ")[1]
        token_info = requests.get(f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}").json()

        if int(token_info["expires_in"]) <= 0 :
            return Response({"error":"access token expired"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if token_info["aud"] != client_id :
            return Response({"error":"wrong access token"}, status=status.HTTP_401_UNAUTHORIZED)
        
        user_info = requests.get(f"https://www.googleapis.com/oauth2/v3/userinfo?access_token={access_token}").json()
        if token_info["sub"] != user_info["sub"]: # to ensure that the user info return belong to the user's token 
            return Response({"error":"wrong user"}, status=status.HTTP_401_UNAUTHORIZED)
        
        user_data = {"email":user_info["email"], "username":user_info["name"],"password":passwordGenerate()}
        try :
            User.objects.get(email = user_data["email"]) 
            response = requests.post("http://127.0.0.1:8000/glogin/", json=user_data).json()
            return Response(response,status=status.HTTP_200_OK)
        
        except ObjectDoesNotExist :
            response = requests.post("http://127.0.0.1:8000/users/", json=user_data).json()
            return Response(response,status=status.HTTP_201_CREATED)
           
def passwordGenerate():
    password=""
    while len(password) < 20:
        password += random.choice(string.printable)
    return password

