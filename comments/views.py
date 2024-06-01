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


class CommentApiView(APIView):
    permission_classes=[IsAuthenticated]


    def post(self, request):
        user = Token.objects.get(key=request.headers["Authorization"].split(' ')[1]).user
        movie = get_object_or_404(Movie,request.data['movie'],"movie doesn't exist")

        data = {
            'text':request.data['text'],
            'movie':movie.pk,
            'user':user.pk,
            'created_at':timezone.now()
        }
        comment_serializer = CommentSerializer(data=data)
        if comment_serializer.is_valid():
            comment_serializer.save()
            return_data = {
                "data":{"action" : "created"},
                "error":None,
                "metadata":{"comments_count":movie.comments_count},
                "status":'success'
            }
            return Response(return_data,status=status.HTTP_201_CREATED)
        
        return Response({"error":"couldn't add comment"},status=status.HTTP_400_BAD_REQUEST)
    
    def put(self ,request, pk=None):
        if 'text' not in request.data:
            raise serializers.ValidationError({"text": "no text provided"})
        try: 
            comment = Comment.objects.get(pk = pk)
        except ObjectDoesNotExist :
            return Response({"error":"no comment provided"},status=status.HTTP_404_NOT_FOUND)
        # check whether the user commented is the same user editing
        if not comment.user == User.objects.get(pk = Token.objects.get(pk = request.headers["Authorization"].split(" ")[1]).user_id) :
            return Response({"error": "trying to edit a reply that doesn't belong to the user"},status=status.HTTP_403_FORBIDDEN)
        comment_serializer = CommentSerializer(comment,data=request.data,partial=True)
        if comment_serializer.is_valid(raise_exception=True):
            comment_serializer.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response({'error': comment_serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request,pk=None):
        user = Token.objects.get(key=request.headers["Authorization"].split(' ')[1]).user
        comment = get_object_or_404(Comment,pk,"Comment does not exist.")
        movie = comment.movie

        if not user == comment.user :
            return Response({"error":"wrong user."}, status=status.HTTP_403_FORBIDDEN)
        
        comment.delete()
        return_data = {
            "data":{"action" : "deleted"},
            "error":None,
            "metadata":{"comments_count":movie.comments_count},
            "status":'success'
        }

        return Response(return_data,status=status.HTTP_200_OK)
       

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
                'replying_to':replying_to.pk,
                'created_at':timezone.now()
            }

            reply_serializer = ReplySerializer(data=data)
            if reply_serializer.is_valid():
                reply_serializer.save()
                return_data = {
                    "data":{"action" : "created"},
                    "error":None,
                    "metadata":{"comments_count":movie.comments_count},
                    "status":'success'
                }
                return Response(return_data,status=status.HTTP_201_CREATED)
            
            return Response({"error":"couldn't add reply"},status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk=None):
        text = request.data['text']
        reply = get_object_or_404(Reply, pk, "reply doesn't exist")
        if not text or len(text) < 1 :
            return Response({"error":"no text provided"},status=status.HTTP_400_BAD_REQUEST)
        user_replying_id = Token.objects.get(key=request.headers['Authorization'].split(" ")[1]).user_id
        user_replying = get_object_or_404(User,user_replying_id, "user doens't exist")
        if not user_replying == reply.user :
            return Response({'error':"forbidden"},status=status.HTTP_403_FORBIDDEN)
        reply_serializer = ReplySerializer(reply, data={'text' : text},partial =True)
        if reply_serializer.is_valid(raise_exception=True) :
            reply_serializer.save()
            return Response({"text":text},status=status.HTTP_200_OK)
        return Response({"error":"reply edit failed"}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request , pk=None) :
        user = Token.objects.get(key=request.headers["Authorization"].split(' ')[1]).user
        reply = get_object_or_404(Reply, pk, "Reply doesn't exist")
        movie = reply.movie

        if not user == reply.user :
            return Response({"error":"wrong user."}, status=status.HTTP_403_FORBIDDEN)
        
        reply.delete()
        return_data = {
            "data":{"action" : "deleted"},
            "error":None,
            "metadata":{"comments_count":movie.comments_count},
            "status":'success'
        }

        return Response(return_data,status=status.HTTP_200_OK)


class CommentReplyApiView(APIView):
    def get(self,request, movie_id=None):
        movie = get_object_or_404(Movie, movie_id,"movie doesn't exist.")
        comments = movie.comments.order_by("-created_at")
        comments_serializer = CommentReplySerializer(comments, many=True)
        returned_data = { 
            "status":"success",
            "error":None,
            "data":{"comments_replies":comments_serializer.data},
            "metadata" : {"comments_replies_count":movie.comments_replies_count}
        }

        return Response(returned_data,status=status.HTTP_200_OK)


class LikesView(APIView):
    # permission_classes = [IsAuthenticated]
    def post(self,request):
        user = Token.objects.get(key= request.headers["Authorization"].split(" ")[1]).user
        comment = Comment.objects.get(id=request.data["id"]) if not request.data["reply"] else Reply.objects.get(id = request.data["id"])
        UserCommentInstance ,created= CommentLikeDislike.objects.get_or_create(user= user,comment=comment,defaults={
        "liked":True,"disliked":False
        }) if not request.data["reply"] else ReplyLikeDislike.objects.get_or_create(user= user,reply=comment,defaults={
        "liked":True,"disliked":False
        })
        if created :
            comment.likes = F("likes") +1
            comment.save(update_fields=["likes"])
            comment.refresh_from_db()

        else :
            if UserCommentInstance.disliked == True :
                UserCommentInstance.disliked = False
                UserCommentInstance.liked =  True
                UserCommentInstance.save(update_fields=["disliked","liked"])
                comment.dislikes = F("dislikes") - 1
                comment.likes = F("likes") + 1
                comment.save(update_fields=["dislikes","likes"])
                comment.refresh_from_db()
            else :
                UserCommentInstance.liked = True if not UserCommentInstance.liked else False
                UserCommentInstance.save(update_fields=["liked",])
                comment.likes = F("likes") + 1 if UserCommentInstance.liked else F("likes")-1 
                comment.save(update_fields=["likes"])
                comment.refresh_from_db()

        return Response({"likes":str(comment.likes),"dislikes":str(comment.dislikes)}, status=status.HTTP_200_OK)

class DislikesView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        user = Token.objects.get(key= request.headers["Authorization"].split(" ")[1]).user
        comment = Comment.objects.get(id=request.data["id"]) if not request.data["reply"] else Reply.objects.get(id = request.data["id"])
        UserCommentInstance ,created= CommentLikeDislike.objects.get_or_create(user= user,comment=comment,defaults={
        "liked":False,"disliked":True
        }) if not request.data["reply"] else ReplyLikeDislike.objects.get_or_create(user= user,reply=comment,defaults={
        "liked":False,"disliked":True
        })
        if created :
            comment.dislikes = F("dislikes") +1
            comment.save(update_fields=["dislikes"]) #update the instance , but it still contain outdated data
            comment.refresh_from_db() #refresh the instance from the database to get the updated latest data

        else :
            if UserCommentInstance.liked == True :
                UserCommentInstance.liked = False
                UserCommentInstance.disliked =  True
                UserCommentInstance.save(update_fields=["disliked","liked"])
                comment.likes = F("likes") - 1
                comment.dislikes = F("dislikes") + 1
                comment.save(update_fields=["dislikes","likes"])
                comment.refresh_from_db()
            else :
                UserCommentInstance.disliked = True if not UserCommentInstance.disliked else False
                UserCommentInstance.save(update_fields=["disliked",])
                comment.dislikes = F("dislikes") + 1 if UserCommentInstance.disliked else F("dislikes")-1 
                comment.save(update_fields=["dislikes"])
                comment.refresh_from_db()
        return Response({"likes":str(comment.likes),"dislikes":str(comment.dislikes)}, status=status.HTTP_200_OK)

class GetLikesDislikesView(APIView):
    def post(self,request):
        comment = Comment.objects.get(id=request.data["id"]) if not request.data["reply"] else Reply.objects.get(id = request.data["id"])
        likes = comment.likes
        dislikes = comment.dislikes
        return Response({"likes":likes,"dislikes":dislikes}, status=status.HTTP_200_OK)
        
