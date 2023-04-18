from rest_framework.response import Response
from rest_framework import viewsets,status
from django.views.decorators.csrf import csrf_exempt
from .models import *
from api.models import Movie
from .serializers import *
from rest_framework.authtoken.models import Token
from django.contrib.auth import login,logout,authenticate
from django.contrib.auth.hashers import check_password
from django.db.models import F
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from oauth2_provider.views import ProtectedResourceView

from rest_framework import serializers
import requests
# from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound
import random 
import string


class UserViewSet(viewsets.ViewSet):
    lookup_field = 'username' # overrides the default field to look for in retrieve, the default is pk 
    serializer_class = UserSerializer
    def list(self, request):
        queryset = User.objects.all()
        serializer = self.serializer_class(queryset, many =True)
        return Response(serializer.data)

    def create(self ,request):
        new_user = request.data
        if User.objects.filter(email = new_user['email']).exists():
            return Response({"error":"Email already used"}, status=status.HTTP_403_FORBIDDEN)
        if User.objects.filter(username = new_user['username']).exists():
            while {'username':new_user['username']} in User.objects.values('username'):
                usernamee = new_user['username']+ " #"+str(random.randrange(1000,99999))
                new_user['username'] =usernamee
                print(new_user['username'])
        new_user['pfp'] = None
        user =User.objects.create_user(username = new_user["username"], email=new_user["email"], password = new_user["password"],pfp=new_user["pfp"])
        token = Token.objects.create(user = user)
        authuser = authenticate(email = new_user['email'], password =new_user['password'])
        if authuser is not None :
            return Response({"user" : self.serializer_class(user).data, "token" : token.key}, status=status.HTTP_201_CREATED)
        else : 
            return Response({"error":"Can't register , check your credentials !"}, status = status.HTTP_400_BAD_REQUEST)
    def retrieve(self, request, username=None):
        try :
            user = User.objects.get(username = username)
            serializer = self.serializer_class(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except :
            return Response("Not Found" , status= status.HTTP_404_NOT_FOUND)
    def update(self, request , username=None):
        pass
    def delete(self,request, username=None):
        pass
class googleLoginViewSet(viewsets.ViewSet):
    def create(self, request):
        email= request.data["email"]
        try :
            user = User.objects.get(email = email)
        except ObjectDoesNotExist:
            return Response({"error": "Wrong email or password 1 !"}, status= status.HTTP_404_NOT_FOUND)
        token = Token.objects.get_or_create(user=user)[0]
        return Response({"user" :UserSerializer(user).data, "token" : token.key},status=status.HTTP_302_FOUND)


class LoginViewSet(viewsets.ViewSet):
    def create(self , request):
        email = request.data["email"]
        password = request.data["password"]
        try :
            user = User.objects.get(email = email)
        except ObjectDoesNotExist:
            return Response({"error": "Wrong email or password 1 !"}, status= status.HTTP_404_NOT_FOUND)
        if not check_password(password, user.password) :
            return Response({"error": "Wrong email or password 2 !"}, status= status.HTTP_404_NOT_FOUND)
        token = Token.objects.get_or_create(user = user)[0]
        return Response({"user" :UserSerializer(user).data, "token" : token.key},status=status.HTTP_302_FOUND)

class LogoutViewSet(viewsets.ViewSet):
    permission_classes =[IsAuthenticated]
    def create(self, request):
        request.user.auth_token.delete()
        return Response({"error":"user logged out"})

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
            user = User.objects.get(email = user_data["email"]) 
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


def Increment_Comments_Number(movie_id,add):
    movie = Movie.objects.get(pk=movie_id)
    if add :
        movie.commentsNumber = F('commentsNumber') + 1
    else : 
        movie.commentsNumber = F('commentsNumber') - 1
    movie.save(update_fields=['commentsNumber'])
    movie.refresh_from_db()
    return movie.commentsNumber

def get_object_or_404(object, pk, error_message):
    try:
        obj = object.objects.get(pk = pk)
        return obj
    except ObjectDoesNotExist:
        raise NotFound(error_message)
        
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
            return_data = {
                "data":cmnt_serializer.data,
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
            parent_comment = get_object_or_404(Comments, request.data['parent-comment-id'], "parent comment not provided")
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




# class CommentReplyApiView(APIView) :
#     permission_classes= [IsAuthenticated]
#     def post(self, request):
#         is_reply =  request.data["reply"]
#         print(request.data)
#         movie = Movie.objects.get(pk = request.data['page_id'])
#         if (is_reply) :
#             data= {
#                 "user":User.objects.get(pk = Token.objects.get(key = request.headers["Authorization"].split(" ")[1]).user_id).id,
#                 "text": request.data["text"],
#                 "date":request.data["dateAdded"],
#                 "parent_comment":Comments.objects.get(pk=request.data['id_replying_to']).id,
#                 "user_replying_to":User.objects.get(username= request.data["username_replying_to"]).id,
#                 "movie_page": request.data["page_id"]
#             }
#             reply = ReplySerializer(data=data)
#             if reply.is_valid():
#                 reply.save()
#                 movie.commentsNumber = F('commentsNumber') + 1
#                 movie.save(update_fields=['commentsNumber'])
#                 movie.refresh_from_db()
#             else:
#                 return Response({"error":"bad request"},status=status.HTTP_400_BAD_REQUEST)
#             comments_count =movie.commentsNumber
#             profile= User.objects.get(username=reply.data['user']).pfp.url if User.objects.get(username=reply.data['user']).pfp else User.objects.get(username = reply.data["user"]).username[0].upper()
#             return Response({"data":reply.data,"pfp":profile,"comments_count":str(comments_count)},status=status.HTTP_200_OK)
#         else :
#             data= {
#                 "user":User.objects.get(pk = Token.objects.get(key = request.headers["Authorization"].split(" ")[1]).user_id).id,
#                 "text": request.data["text"],
#                 "date":request.data["dateAdded"],
#                 "movie_page": request.data["page_id"]
#             }
#             comment = CommentSerializer(data=data)
#             movie = Movie.objects.get(pk = request.data['page_id'])
#             if comment.is_valid():
#                 comment.save()
#                 movie.commentsNumber = F('commentsNumber') + 1
#                 movie.save(update_fields=['commentsNumber'])
#                 movie.refresh_from_db()
#             else:
#                 print(comment.errors)
#                 return Response({"error":"bad request"},status=status.HTTP_400_BAD_REQUEST)
#             profile= User.objects.get(pk=comment.data['user']).pfp.url if User.objects.get(pk=comment.data['user']).pfp else User.objects.get(pk = comment.data["user"]).username[0].upper()
#             comments_count =movie.commentsNumber
#             return Response({"data":comment.data,"pfp":str(profile),"comments_id":Comments.objects.count(),"comments_count":str(comments_count)},status = status.HTTP_200_OK)
#     def put(self,request):
#         pass


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
        return Response({"error":"No comments Yet !"},status=status.HTTP_404_NOT_FOUND)


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
        
