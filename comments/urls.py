from django.urls import path
from .views import *


urlpatterns = [
    path('comments/',CommentApiView.as_view(),name="comments"),
    path('comments/<int:pk>',CommentApiView.as_view(),name="comments"),

    path('replies/',ReplyApiView.as_view(),name="replies"),
    path('replies/<int:pk>',ReplyApiView.as_view(),name="replies"),

    path('movies/<int:movie_id>/comments-and-replies/',CommentReplyApiView.as_view(),),

    path("like/", LikesView.as_view(),),
    path("dislike/", DislikesView.as_view(),),
    path("getlikesdislikes/",GetLikesDislikesView.as_view(),),
]