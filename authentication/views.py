from rest_framework.response import Response
from rest_framework import viewsets,status
from django.views.decorators.csrf import csrf_exempt
from .models import *
from api.models import Movie
from .serializers import *
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import check_password
from django.db.models import F
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from oauth2_provider.views import ProtectedResourceView
from django.core.files.storage import default_storage
from rest_framework import serializers
import requests
# from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound
from rest_framework.decorators import permission_classes
import random 
import string

def get_object_or_404(object, pk, error_message):
    try:
        obj = object.objects.get(pk = pk)
        return obj
    except ObjectDoesNotExist:
        raise NotFound(error_message)
        
def remove_tuples_from_list(arr, *args):
    for key in args :
        for item in arr :
            if item[0] == key:
                arr.remove(item)
                print(item)
    print(arr)
    return arr
    

class UserViewSet(viewsets.ViewSet):
    lookup_field = 'pk' # overrides the default field to look for in retrieve, the default is pk 
    serializer_class = UserSerializer

    # apply isAuthenticated permission check to partial_update method only
    def get_permissions(self):
        if self.request.method == "PATCH":
            # permission list is used by check_permissions() method 
            return [IsAuthenticated()]
        # return [permission() for permission in permission_classes]
        return super().get_permissions()
    
    def list(self, request):
        queryset = User.objects.all()
        serializer = self.serializer_class(queryset, many =True)
        return Response(serializer.data)

    def create(self ,request):
        new_user = request.data
        if User.objects.filter(email = new_user['email']).exists():
            return Response({"error":"Email already used"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username = new_user['username']).exists():
            while {'username':new_user['username']} in User.objects.values('username'):
                usernamee = new_user['username']+ " #"+str(random.randrange(1000,99999))
                new_user['username'] =usernamee
        new_user['pfp'] = None
        user =User.objects.create_user(username = new_user["username"], email=new_user["email"], password = new_user["password"],pfp=new_user["pfp"])
        token = Token.objects.create(user = user)
        return Response({"user" : self.serializer_class(user).data, "token" : token.key}, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        try :
            user = User.objects.get(pk = pk)
            serializer = self.serializer_class(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except :
            return Response("Not Found" , status= status.HTTP_404_NOT_FOUND)
        
    def partial_update(self, request , pk=None):
        # get the user that sent the request
        requester_user = Token.objects.get(key = request.headers["Authorization"].split(" ")[1]).user
        # get the user who's information to be updated
        user = get_object_or_404(User,pk,"user does not exist")
        # check if both if the user who sent the request has the info to be updated
        if not (requester_user == user):
            return Response({"error": "not authorized"}, status=status.HTTP_403_FORBIDDEN)
        # remove empty info from the request's body
        user_info = {i:request.data[i] for i in request.data if not (len(request.data[i]) == 0)}
        
        # check if the new email is in the info to be updated
        if "email" in user_info :
            try:
                #get the user of the email to be updated
                user_by_email = User.objects.get(email = user_info["email"])
                #if email is the same as the original , remove it from the info to be updated
                if user == user_by_email :
                    user_info.pop("email")
                #if the client is updating his email to an email that belongs to another user, send an error response
                else :
                    return Response({"error":"email already used"}, status = status.HTTP_400_BAD_REQUEST)
            # if the email is not used and different from the original , continue 
            except ObjectDoesNotExist:
                pass
        # if password is in requests body , update it alone
        if "newPassword" in user_info and user_info["newPassword"] :
            # check if old password is correct
            if not check_password(user_info['oldPassword'],user.password):
                return Response({"error":"old password is not correct"},status=status.HTTP_400_BAD_REQUEST)
            #check if new password and confirm password are equal 
            if not user_info["newPassword"] == user_info["confirmPassword"]:
                return Response({"error":"passwords don't match"},status=status.HTTP_400_BAD_REQUEST)
            # update the password of the user
            user.set_password(user_info['newPassword'])
            # update the password of the instance in the database
            user.save(update_fields=["password"])
        # create a new array of user's info without the passwords (already updated)
        cleaned_array = remove_tuples_from_list(list(user_info.items()),"newPassword","oldPassword","confirmPassword") 
        # the message to be sent in the response ,(contains updated info)
        response_message = {}
        # update the fields of the user model by the cleaned array (password already updated)
        # equivalent to : user.email = email , user.username = username ...
        for info, value in cleaned_array:
            setattr(user, info, value)
            response_message[info] = value
        # update the row in the db (only update changed fields)
        user.save(update_fields=[i[0] for i in cleaned_array])
        print(response_message)
        return Response(response_message, status=status.HTTP_200_OK)                                           
    def delete(self,request, pk=None):
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
        
