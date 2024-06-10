from django.shortcuts import render
from api.models import Movie
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from authentication.views import get_object_or_404
from django.db.models import F
from rest_framework.authtoken.models import Token
from .serializers import CommentSerializer,ReplySerializer, CommentReplySerializer
from rest_framework.response import Response
from rest_framework import serializers
from authentication.models import User
from .models import Comment, Reply, CommentLikeDislike, ReplyLikeDislike
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets,status
from django.utils import timezone
from helpers.response import successResponse, failedResponse
from .services import LikeDislikeService


class CommentApiView(APIView):
    permission_classes=[IsAuthenticated]

    def post(self, request):
        user = request.user
        movie = get_object_or_404(Movie,request.data['movie'],"movie doesn't exist")

        data = {
            'text':request.data['text'],
            'movie':movie.pk,
            'user':user.pk,
            'created_at':timezone.now()
        }

        comment_serializer = CommentSerializer(data=data)
        if comment_serializer.is_valid():
            new_comment = comment_serializer.save()

            data = {"action" : "created",'comment' : CommentReplySerializer(new_comment).data}
            metadata = {"comments_replies_count":movie.comments_replies_count}
            payload = successResponse(data, metadata)

            return Response(payload,status=status.HTTP_201_CREATED)
        
        return Response({"error":"couldn't add comment"},status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk=None) : 
        text = (request.data['text'] or "").strip()

        if len(text) <= 0 : 
            error = {"message":"Text was not provided.", "code" : 400}
            payload = failedResponse(error, None)
            return Response(payload,status=status.HTTP_400_BAD_REQUEST)
        
        comment = get_object_or_404(Comment, pk, "Comment doesn't exist.")

        user_requesting = request.user
        user_of_comment = comment.user

        if not user_requesting == user_of_comment :
            error = {"message":"You are not allowed to patch other users' comments", "code" : 403}
            payload = failedResponse(error, None)
            return Response(payload,status=status.HTTP_403_FORBIDDEN)
        
        comment_serializer = CommentSerializer(comment, data={'text' : text}, partial=True)
        if comment_serializer.is_valid() :
            comment_serializer.save()

            payload = successResponse({'comment' : {'text' : text}},None)
            return Response(payload, status.HTTP_200_OK)

        failedResponse({"message" : "Invalid data." , "details" : comment_serializer.errors, "code" : 400},None)
        return Response(payload, status.HTTP_200_OK)
    
        
    def delete(self, request,pk=None):
        user = Token.objects.get(key=request.headers["Authorization"].split(' ')[1]).user
        comment = get_object_or_404(Comment,pk,"Comment does not exist.")
        movie = comment.movie

        if not user == comment.user :
            return Response({"error":"wrong user."}, status=status.HTTP_403_FORBIDDEN)
        
        comment.delete()
        payload = {
            "data":{"action" : "deleted"},
            "error":None,
            "metadata":{"comments_replies_count":movie.comments_replies_count},
            "status":'success'
        }

        return Response(payload,status=status.HTTP_200_OK)
       

class ReplyApiView(APIView):
    permission_classes=[IsAuthenticated]

    def post(self,request):
            user = Token.objects.get(key=request.headers["Authorization"].split(' ')[1]).user
            parent_comment = get_object_or_404(Comment, request.data['parent_comment'], "parent comment not provided")
            movie = get_object_or_404(Movie, request.data['movie'],"movie doesn't exist")
            replying_to = None

            if parent_comment.id !=  request.data["replying_to"]:
                replying_to = get_object_or_404(Reply, request.data['replying_to'], "comment you are replying to does not exist.")

            data= {
                'user':user.pk,
                'parent_comment': parent_comment.pk,
                'text':request.data['text'],
                'movie':movie.pk,
                'replying_to':getattr(replying_to, 'pk' , None),
                'created_at':timezone.now()
            }

            reply_serializer = ReplySerializer(data=data)
            if reply_serializer.is_valid():
                new_reply = reply_serializer.save()
                
                data ={"action" : "created","reply" :ReplySerializer(new_reply).data}
                metadata ={"comments_replies_count":movie.comments_replies_count}
                payload = successResponse(data, metadata)

                return Response(payload,status=status.HTTP_201_CREATED)
            
            error = {"message":"couldn't add reply", "code" : 400}
            payload = failedResponse(error, None)
            return Response(payload,status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk=None) : 
        text = (request.data['text'] or "").strip()

        if len(text) <= 0 : 
            error = {"message":"Text was not provided.", "code" : 400}
            payload = failedResponse(error, None)
            return Response(payload,status=status.HTTP_400_BAD_REQUEST)
        
        reply = get_object_or_404(Reply, pk, "Reply doesn't exist.")

        user_requesting = request.user
        user_of_reply = reply.user

        if not user_requesting == user_of_reply :
            error = {"message":"You are not allowed to patch other users' replies", "code" : 403}
            payload = failedResponse(error, None)
            return Response(payload,status=status.HTTP_403_FORBIDDEN)
        
        reply_serializer = ReplySerializer(reply, data={'text' : text}, partial=True)
        if reply_serializer.is_valid() :
            reply_serializer.save()

            payload = successResponse({'reply' : {'text' : text}},None)
            return Response(payload, status.HTTP_200_OK)

        failedResponse({"message" : "Invalid data." , "details" : reply_serializer.errors, "code" : 400},None)
        return Response(payload, status.HTTP_200_OK)
    
    def delete(self, request , pk=None) :
        user = Token.objects.get(key=request.headers["Authorization"].split(' ')[1]).user
        reply = get_object_or_404(Reply, pk, "Reply doesn't exist")
        movie = reply.movie

        if not user == reply.user :
            return Response({"error":"wrong user."}, status=status.HTTP_403_FORBIDDEN)
        
        reply.delete()
        payload = {
            "data":{"action" : "deleted"},
            "error":None,
            "metadata":{"comments_replies_count":movie.comments_replies_count},
            "status":'success'
        }

        return Response(payload,status=status.HTTP_200_OK)


class CommentReplyApiView(APIView):
    def get(self,request, movie_id=None):
        movie = get_object_or_404(Movie, movie_id,"movie doesn't exist.")
        comments = movie.comments.order_by("-created_at")

        comments_serializer = CommentReplySerializer(comments, many=True, context={"request" : request})
        data = {"comments_replies":comments_serializer.data}
        metadata = {"comments_replies_count":movie.comments_replies_count}
        
        payload = successResponse(data,metadata)
        return Response(payload,status=status.HTTP_200_OK)


class CommentLikeApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request, pk):
        like_dislike_service = LikeDislikeService(Comment, CommentLikeDislike)
        dict_result = like_dislike_service.like(request, pk)

        payload = {"action" : dict_result['action']}
        metadata = {"dislikes_count" : dict_result['dislikes_count'], "likes_count" : dict_result['likes_count']}

        return Response(successResponse(payload,metadata), status.HTTP_200_OK)

class CommentDislikeApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request, pk):
        like_dislike_service = LikeDislikeService(Comment, CommentLikeDislike)
        dict_result = like_dislike_service.dislike(request, pk)

        payload = {"action" : dict_result['action']}
        metadata = {"dislikes_count" : dict_result['dislikes_count'], "likes_count" : dict_result['likes_count']}
        
        return Response(successResponse(payload,metadata), status.HTTP_200_OK)
        


class ReplyLikeApiView(APIView) :
    permission_classes = [IsAuthenticated]

    def post(self,request, pk):
        like_dislike_service = LikeDislikeService(Reply, ReplyLikeDislike)
        dict_result = like_dislike_service.like(request, pk)

        payload = {"action" : dict_result['action']}
        metadata = {"dislikes_count" : dict_result['dislikes_count'], "likes_count" : dict_result['likes_count']}
        
        return Response(successResponse(payload,metadata), status.HTTP_200_OK)

class ReplyDislikeApiView(APIView) :
    permission_classes = [IsAuthenticated]

    def post(self,request, pk):
        like_dislike_service = LikeDislikeService(Reply, ReplyLikeDislike)
        dict_result = like_dislike_service.dislike(request, pk)

        payload = {"action" : dict_result['action']}
        metadata = {"dislikes_count" : dict_result['dislikes_count'], "likes_count" : dict_result['likes_count']}
        
        return Response(successResponse(payload,metadata), status.HTTP_200_OK)
    

class GetLikesDislikesView(APIView):
    def post(self,request):
        comment = Comment.objects.get(id=request.data["id"]) if not request.data["reply"] else Reply.objects.get(id = request.data["id"])
        likes = comment.likes
        dislikes = comment.dislikes
        return Response({"likes":likes,"dislikes":dislikes}, status=status.HTTP_200_OK)
        
