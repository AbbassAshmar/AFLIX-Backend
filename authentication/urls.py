from django.urls import path,include
from .views import *
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r'users',UserViewSet, basename="user")
router.register(r'login', LoginViewSet, basename="login")
router.register(r'logout', LogoutViewSet, basename="logout")
router.register(r'glogin',googleLoginViewSet,basename='glogin')

urlpatterns =[
    path('', include(router.urls)),
    path('validate/', TokenValidate.as_view()),
]