from django.urls import path,include
from .views import *
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r'users',UserViewSet, basename="users")
router.register(r'login', LoginViewSet, basename="login")
router.register(r'logout', LogoutViewSet, basename="logout")
router.register(r'glogin',googleLoginViewSet,basename='glogin')
urlpatterns =[
    path('', include(router.urls)),
    path('validate/', TokenValidate.as_view()),
    
    path('comments/',CommentApiView.as_view(),name="comments"),
    path('comments/<int:pk>',CommentApiView.as_view(),name="comments"),

    path('replies/',ReplyApiView.as_view(),name="replies"),
    path('replies/<int:pk>',ReplyApiView.as_view(),name="replies"),

    path('allcomments/',AllComents.as_view(),),
    path("like/", LikesView.as_view(),),
    path("dislike/", DislikesView.as_view(),),
    path("getlikesdislikes/",GetLikesDislikesView.as_view(),),
]