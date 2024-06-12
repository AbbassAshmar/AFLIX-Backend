from rest_framework.response import Response
from rest_framework import viewsets,status
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
import requests
from helpers.response import successResponse, failedResponse
from rest_framework.generics import CreateAPIView,UpdateAPIView
from .services import UserService
from django.http import Http404
from rest_framework.exceptions import NotFound

def remove_tuples_from_list(arr, *args):
    for key in args :
        for item in arr :
            if item[0] == key:
                arr.remove(item)
    return arr

class UserViewSet(viewsets.ModelViewSet):
    lookup_field = 'pk'
    serializer_class = UserSerializer
    queryset = User.objects.all()
    
    def get_object(self):
        try : 
            return super().get_object()
        except Http404 : 
            raise NotFound("User not found.")
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        payload = successResponse({'users' : response.data}, None)
        return Response(payload, status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        payload = successResponse({'user' : response.data}, None)
        return Response(payload, status.HTTP_200_OK)
        
class UpdateUserApiView(UpdateAPIView) : 
    lookup_field = 'pk'
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def partial_update(self, request):
        user = request.user
        new_data = request.data
        updated_fields = [key for key in request.data.keys() if request.data[key]]
        
        user = UserService.update_user(user, new_data)
        data = {"user" : UserSerializer(user,context={"fields":updated_fields}).data}

        payload = successResponse(data,None)
        return Response(payload, status=status.HTTP_200_OK)                             

class googleLoginViewSet(viewsets.ViewSet):
    def create(self, request):
        email= request.data["email"]
        try :
            user = User.objects.get(email = email)
        except ObjectDoesNotExist:
            return Response({"error": "Wrong email or password 1 !"}, status= status.HTTP_404_NOT_FOUND)
        token = Token.objects.get_or_create(user=user)[0]
        return Response({"user" :UserSerializer(user).data, "token" : token.key},status=status.HTTP_302_FOUND)

class RegisterApiView(CreateAPIView):
    permission_classes= []
    serializer_class = UserSerializer

    def post(self , request):
        data= request.data
        user = UserService.create_user(data)
        token = UserService.create_token(user)

        data = {
            "user" : self.get_serializer(user).data,
            "token" : token.key
        }

        payload = successResponse(data, None)
        return Response(payload, status=status.HTTP_201_CREATED)
        
class LoginApiView(CreateAPIView):
    def post(self , request):
        email , password = request.data.get('email', None), request.data.get('password', None)
        user = UserService.get_user_with_email_password(email , password)
        token = UserService.create_token(user)

        data= {
            "user" : UserSerializer(user).data,
            'token' : token.key
        }
        
        payload = successResponse(data, None)
        return Response(payload,status=status.HTTP_200_OK)

class LogoutApiView(CreateAPIView):
    permission_classes =[IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        data= {"action" : "logged out"}
        return Response(successResponse(data,None), status.HTTP_200_OK)

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

