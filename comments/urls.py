from django.urls import path
from .views import *


urlpatterns = [
    path('comments/',CommentApiView.as_view(),name="comments"),
    path('comments/<int:pk>',CommentApiView.as_view(),name="comments"),

    path('replies/',ReplyApiView.as_view(),name="replies"),
    path('replies/<int:pk>',ReplyApiView.as_view(),name="replies"),

    path('movies/<int:movie_id>/comments-and-replies/',CommentReplyApiView.as_view(),),

    path("comments/<int:pk>/likes/", CommentLikeApiView.as_view(),name="comments-like"),
    path("comments/<int:pk>/dislikes/", CommentDislikeApiView.as_view(),name="comments-dislike"),

    path("replies/<int:pk>/likes/", ReplyLikeApiView.as_view(),name="replies-like"),
    path("replies/<int:pk>/dislikes/", ReplyDislikeApiView.as_view(),name="replies-dislike"),

    path("getlikesdislikes/",GetLikesDislikesView.as_view(),),
]