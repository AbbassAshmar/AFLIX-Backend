from rest_framework.response import Response
from rest_framework import viewsets,status
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from helpers.response import successResponse, failedResponse
from rest_framework.generics import CreateAPIView,UpdateAPIView
from .services import UserService,GoogleAuthService
from django.http import Http404
from rest_framework.exceptions import NotFound
from dotenv import load_dotenv, find_dotenv
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
import os

load_dotenv(find_dotenv())


class IgnoreInvalidToken(TokenAuthentication):
    def authenticate_credentials(self, key):
        try:
            return super().authenticate_credentials(key)
        except AuthenticationFailed:
            return None  
        
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


class RegisterApiView(CreateAPIView):
    permission_classes= []
    serializer_class = UserSerializer

    def post(self , request):
        data= request.data
        user = UserService.register_user(data)
        token = UserService.create_token(user)

        data = {
            "user" : self.get_serializer(user).data,
            "token" : token.key
        }

        payload = successResponse(data, None)
        return Response(payload, status=status.HTTP_201_CREATED)
        
class LoginApiView(CreateAPIView):
    permission_classes = [IgnoreInvalidToken]

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

class GoogleRegisterApiView(CreateAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        access_token = request.data.get("access_token",None)
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        google_auth = GoogleAuthService(access_token, client_id)

        user = google_auth.authenticate_user()
        token = UserService.create_token(user)

        data = {"user" : self.get_serializer(user).data, "token" : token.key}
        payload = successResponse(data, None)

        return Response(payload,status=status.HTTP_200_OK)


