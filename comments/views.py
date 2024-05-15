from django.shortcuts import render
from api.models import Movie
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from authentication.views import get_object_or_404
from django.db.models import F
from rest_framework.authtoken.models import Token
from .serializers import CommentSerializer,ReplySerializer,CommentReplySerializer
from rest_framework.response import Response
from rest_framework import serializers
from authentication.models import User
from .models import Comments, Replies, CommentsLikesDislike, RepliesLikesDislike
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets,status

def Increment_Comments_Number(movie_id,add):
    movie = Movie.objects.get(pk=movie_id)
    if add :
        movie.commentsNumber = F('commentsNumber') + 1
    else : 
        movie.commentsNumber = F('commentsNumber') - 1
    movie.save(update_fields=['commentsNumber'])
    movie.refresh_from_db()
    return movie.commentsNumber


class CommentApiView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request):
        movie = get_object_or_404(Movie,request.data['page_id'],"movie doesn't exist")
        data = {
            'text':request.data['text'],
            'movie_page':movie.pk,
            'user':Token.objects.get(key=request.headers["Authorization"].split(' ')[1]).user_id,
            'date':request.data['dateAdded']
        }
        cmnt_serializer = CommentSerializer(data=data)
        if cmnt_serializer.is_valid():
            cmnt_serializer.save()
            comments_number = Increment_Comments_Number(request.data['page_id'],True)
            user_commented = User.objects.get(pk=cmnt_serializer.data['user'])
            profile= user_commented.pfp.url if user_commented.pfp else user_commented.username[0].upper()
            response_data = cmnt_serializer.data
            response_data['user']= user_commented.username
            return_data = {
                "data":response_data,
                "comments_count":str(comments_number),
                "pfp":str(profile),
            }
            return Response(return_data,status=status.HTTP_200_OK)
        return Response({"error":"couldn't add comment"},status=status.HTTP_400_BAD_REQUEST)
    def put(self ,request, pk=None):
        if 'text' not in request.data:
            raise serializers.ValidationError({"text": "no text provided"})
        try: 
            comment = Comments.objects.get(pk = pk)
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
        try : 
            comment = Comments.objects.get(pk = pk)
            movie = comment.movie_page
            comment.delete()
            comments_number = Increment_Comments_Number(movie.pk, False)
            return Response({"comments_count":comments_number},status=status.HTTP_200_OK)
        except ObjectDoesNotExist as e:
            return Response({"error" : e}, status=status.HTTP_404_NOT_FOUND)

class ReplyApiView(APIView):
    permission_classes=[IsAuthenticated]

    def post(self,request):
            parent_comment = get_object_or_404(Comments, request.data['parent_comment_id'], "parent comment not provided")
            movie = get_object_or_404(Movie, request.data['page_id'],"movie doesn't exist")

            try:
                user_replying_to = User.objects.get(username = request.data["username_replying_to"])
            except :
                return Response({"error":"no user to reply to"},status=status.HTTP_404_NOT_FOUND)
            
            user_replied = User.objects.get(pk=Token.objects.get(key=request.headers["Authorization"].split(' ')[1]).user_id)
            data= {
                'user':user_replied.pk,
                'parent_comment': parent_comment.pk,
                'text':request.data['text'],
                'page_id':movie.pk,
                'user_replying_to':user_replying_to.pk,
                'date':request.data['dateAdded']
            }

            reply_serializer = ReplySerializer(data=data)
            if reply_serializer.is_valid():
                reply_serializer.save()
                comments_count = Increment_Comments_Number(movie.pk,True)
                profile= user_replied.pfp.url if user_replied.pfp else user_replied.username[0].upper()
                resp = {
                    'data': reply_serializer.data,
                    'comments_count' :comments_count,
                    'pfp':profile
                }
                return Response(resp,status=status.HTTP_200_OK)
            
            return Response({"error":"couldn't add reply"},status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk=None):
        text = request.data['text']
        reply = get_object_or_404(Replies, pk, "reply doesn't exist")
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
        user_id = Token.objects.get(key= request.headers["Authorization"].split(' ')[1]).user_id
        user = get_object_or_404(User, user_id, "User doesn't exist")
        reply = get_object_or_404(Replies, pk, "Reply doesn't exist")
        movie = reply.movie_page
        if not user == reply.user :
            return Response({"error":"wrong user"}, status=status.HTTP_403_FORBIDDEN)
        reply.delete()
        comments_count = Increment_Comments_Number(movie.id, False)
        return Response({"comments_count":comments_count},status=status.HTTP_200_OK)


class ListCommentsRepliesApiView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request, pk=None):
        movie = get_object_or_404(Movie, pk,"movie doesn't exist")
        comments = Comments.objects.filter(movie_page = movie).order_by("-date")
        if comments.exists():
            commentsSerializer = CommentReplySerializer(comments,many=True)
            returned_data = { 
                "comments-replies":commentsSerializer.data,
                "comments_count":movie.commentsNumber
            }
            return Response(returned_data,status=status.HTTP_200_OK)
        
        returned_data = {
            "comments-replies":[],
            "comments_count":0,
            "error":"No comments Yet !"  
        }
        return Response(returned_data,status=status.HTTP_404_NOT_FOUND)


class LikesView(APIView):
    # permission_classes = [IsAuthenticated]
    def post(self,request):
        user = Token.objects.get(key= request.headers["Authorization"].split(" ")[1]).user
        comment = Comments.objects.get(id=request.data["id"]) if not request.data["reply"] else Replies.objects.get(id = request.data["id"])
        UserCommentInstance ,created= CommentsLikesDislike.objects.get_or_create(user= user,comment=comment,defaults={
        "liked":True,"disliked":False
        }) if not request.data["reply"] else RepliesLikesDislike.objects.get_or_create(user= user,reply=comment,defaults={
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
        comment = Comments.objects.get(id=request.data["id"]) if not request.data["reply"] else Replies.objects.get(id = request.data["id"])
        UserCommentInstance ,created= CommentsLikesDislike.objects.get_or_create(user= user,comment=comment,defaults={
        "liked":False,"disliked":True
        }) if not request.data["reply"] else RepliesLikesDislike.objects.get_or_create(user= user,reply=comment,defaults={
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
        comment = Comments.objects.get(id=request.data["id"]) if not request.data["reply"] else Replies.objects.get(id = request.data["id"])
        likes = comment.likes
        dislikes = comment.dislikes
        return Response({"likes":likes,"dislikes":dislikes}, status=status.HTTP_200_OK)
        
