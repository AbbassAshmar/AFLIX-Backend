from django.urls import path,include
from .views import *
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r'users',UserViewSet, basename="user")

urlpatterns =[
    path('google/register', GoogleRegisterApiView.as_view()),
    path("login", LoginApiView.as_view(), name="login"),
    path("register", RegisterApiView.as_view(), name="register"),
    path("logout", LogoutApiView.as_view(), name="logout"),
    path("users", UpdateUserApiView.as_view(), name="partial-update-user"),
    path('', include(router.urls)),
]