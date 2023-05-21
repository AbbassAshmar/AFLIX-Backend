from django.test import TestCase
from api.models import Movie, Directors, Genre
from rest_framework.authtoken.models import Token
from authentication.models import User, Comments, Replies
from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from .views import CommentApiView

class Test_User(TestCase):
    # executes only once initially
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(username="user1", email="user1@gmail.com",password="user12345")
        cls.user2 = User.objects.create_user(username="user2", email="user2@gmail.com",password="user23456")
        cls.user3 = User.objects.create_user(username="user3", email="user3@gmail.com",password="user33456")
    # executes with each test
    def setUp(self):
        token ,created=Token.objects.get_or_create(user=self.user1)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    def test_user_partial_update(self):
        new_info ={
            "username" :"user11",
            "email":"user111@gmail.com"
        }
        request_update = self.client.patch(reverse("user-detail",args=[self.user1.pk]),data=new_info)
        self.assertEqual(request_update.status_code, 200)
        self.assertDictEqual(new_info,request_update.json())
        user = User.objects.filter(pk = self.user1.pk).values("username","email")[0]
        self.assertDictEqual(new_info,user)
    def test_user_partial_update_fail_wrong_user(self):
        new_info ={
            "username" :"user11",
            "email":"user111@gmail.com"
        }
        request_update = self.client.patch(reverse("user-detail",args=[self.user2.pk]),data=new_info) #user1 updating user2's info
        self.assertEqual(request_update.status_code, 403)
        user = User.objects.filter(pk = self.user2.pk).values("username","email")[0]
        self.assertNotEqual(new_info,user)
    def test_user_partial_update_fail_email_already_used(self):
        new_info= {
            "email":"user2@gmail.com"
        }
        request_update = self.client.patch(reverse("user-detail",args=[self.user1.pk]),data=new_info) #email belongs to user2
        self.assertEqual(request_update.status_code, 400)
        self.assertEqual(request_update.json()["error"],"email already used")
        user = User.objects.filter(pk = self.user1.pk).values("email")[0]
        self.assertNotEqual(new_info, user)
    


class Test_Comment(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="ss@gmail.com",username="ssa",password="asderfds")
        cls.token = Token.objects.create(user=cls.user)
        cls.movie = Movie.objects.create(
        pk=1,
        commentsNumber=1,
        title="iew",
        trailer="www.sdiojfdsijfiejwfijwoifj",
        image="www.sdiojfdsijfiejwfijwoifj",
        thumbnail="www.sdiojfdsijfiejwfijwoifj",
        imdbId='fsdfewfwerew',
        poster="www.sdiojfdsijfiejwfijwoifj",
        ratings={"imdb":"N/A","metacritics":"N/A"},
        plot="N/A",
        contentRate="N/A",
        duration=234,
        released="2024-04-04",
        director=Directors.objects.create(name="John Snow"))
        cls.cmnt = Comments.objects.create(user=cls.user,
        profile = cls.user,
        movie_page=cls.movie,
        text="anidfjo",)
        cls.reply1 = Replies.objects.create(user = cls.user,
        profile=cls.user,
        parent_comment =cls.cmnt,
        user_replying_to = cls.user)
        cls.cmnt.user_ld.add(cls.user)
        cls.reply1.user_ld.add(cls.user)
    def test_cmnt_create(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        data={
            'text':"jfwori",
            'page_id':1,
            'dateAdded':'2023-03-25T15:07:54Z'
        }
        request =self.client.post(reverse('comments'),data)
        self.assertEqual(request.status_code,200)
        self.assertEqual(request.json()['comments_count'], '2')
    def test_cmnt_edit(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        request_body = {
            "text":"anytext",
        }   
        request = self.client.put(reverse('comments', args=['1']), request_body)     
        self.assertEqual(request.status_code, 200)
        self.comment_new_text = Comments.objects.get(pk=1).text
        self.assertEqual(self.comment_new_text, request_body['text'])
        request = self.client.put(reverse('comments', args=['1']))
        self.assertEqual(request.status_code, 400)
    def test_cmnt_edit_fail_forbidden(self):

        #create a new coment with a different user
        new_user = User.objects.create_user(email="ssss@gmail.com",username="sssa",password="asdfderfds") 
        comment = Comments.objects.create(
        pk = 2,
        user=new_user,
        profile = new_user,
        movie_page=self.movie,
        text="anidfjo",)
        comment.user_ld.add(new_user)

        #edit the comment with the first user
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        request = self.client.put(reverse('comments', args=['2']), {"text":"anytext",})     
        self.assertEqual(request.status_code, 403)

    def test_comment_delete(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.reply = Replies.objects.get(parent_comment=self.cmnt)
        self.assertIsInstance(self.reply,Replies)
        request = self.client.delete(reverse("comments", args=['1']))
        self.assertEqual(request.status_code, 200)
        self.assertEqual(request.json()['comments_count'],0)
        with self.assertRaises(ObjectDoesNotExist) : 
            Comments.objects.get(pk = 1)
        with self.assertRaises(ObjectDoesNotExist):
            Replies.objects.get(parent_comment=self.cmnt)



class Test_Replies(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="ss3@gmail.com",username="ssa",password="asderfds")
        cls.movie = Movie.objects.create(
        pk=1,
        title="iew",
        trailer="www.sdiojfdsijfiejwfijwoifj",
        image="www.sdiojfdsijfiejwfijwoifj",
        thumbnail="www.sdiojfdsijfiejwfijwoifj",
        imdbId='fsdfewfwerew',
        poster="www.sdiojfdsijfiejwfijwoifj",
        ratings={"imdb":"N/A","metacritics":"N/A"},
        plot="N/A",
        contentRate="N/A",
        duration=234,
        released="2024-04-04",
        commentsNumber = 1,
        director=Directors.objects.create(name="John Snow"))
        cls.cmnt = Comments.objects.create(pk=1,user=cls.user,
        profile = cls.user,
        movie_page=cls.movie,
        text="anidfjo",)
        cls.cmnt.user_ld.add(cls.user)
    def setUp(self):
        self.token ,created= Token.objects.get_or_create(user = self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
    def test_reply_create(self):
        data = {
           'text' :"aadifj",
           'parent_comment_id':"1",
           "username_replying_to":"ssa",
           "dateAdded":'2023-03-25T15:07:54Z',
           "page_id":'1'
        }
        request = self.client.post(reverse('replies'), data=data)
        self.assertEqual(request.status_code, 200)
        reply = Replies.objects.get(pk=2)
        self.assertIsInstance(reply, Replies)
        self.assertEqual(request.json()['comments_count'] , 2)
        self.assertEqual(reply.parent_comment.pk,1)
    def test_reply_create_fail_user_fail(self):
        
        data={
            'text':"fwiefj",
            'parent_comment_id':"1",
            "username_replying_to":"ssfijeowa",#user doesn't exist
            "dateAdded":'2023-03-25T15:07:54Z',
            "page_id":'1'
        }
        request = self.client.post(reverse('replies'), data = data)
        self.assertEqual(request.status_code, 404)
    def test_reply_create_fail_comment_fail(self):
        data={
            'text':"fwiefj",
            'parent_comment_id':"5",#comment doesn't exist
            "username_replying_to":"ssa",
            "dateAdded":'2023-03-25T15:07:54Z',
            "page_id":'1'
        }
        request = self.client.post(reverse('replies'), data = data)
        self.assertEqual(request.status_code, 404)
    def test_reply_create_fail_page_id_fail(self):
        data={
            'text':"fwiefj",
            'parent_comment_id':"1",
            "username_replying_to":"ssa",
            "dateAdded":'2023-03-25T15:07:54Z',
            "page_id":'6'#page id doesn't exist
        }
        request = self.client.post(reverse('replies'), data = data)
        self.assertEqual(request.status_code, 404)
    def test_reply_edit(self):
        reply =Replies.objects.create(
            pk = 3,
            user = self.user,
            text="aaa",
            parent_comment=self.cmnt,
            user_replying_to=self.user,
            movie_page=self.movie,
        )
        request = self.client.put(reverse("replies", args=['3']), data={"text":"bbb"})
        self.assertEqual(request.status_code, 200)
        self.assertIn('text',request.json())
        reply = Replies.objects.get(pk =3)
        self.assertEqual(reply.text, "bbb")
    def text_reply_edit_fail_no_text_provided(self):
        reply =Replies.objects.create(
            pk=5,
            user = self.user,
            text="aaa",
            parent_comment=self.cmnt,
            user_replying_to=self.user,
            movie_page=self.movie,
        )
        
        self.assertEqual(reply.text,"aaa")
        data={
            'text':"",
        }
        request = self.client.put(reverse("replies", args=['5',]), data=data)
        self.assertEqual(request.status_code, 400)
        reply = Replies.objects.get(pk =5)
        self.assertEqual(request.json()['error'], "no text provided")
        self.assertEqual(reply.text, "aaa")
    def test_reply_edit_doesnt_exist(self):
        reply = Replies.objects.create(
            pk = 4,
            user = self.user,
            text="aaa",
            parent_comment=self.cmnt,
            user_replying_to=self.user,
            movie_page=self.movie,
        )
        self.assertEqual(reply.text,"aaa")
        data = {
            'text':"bbb",
        }
        request = self.client.put(reverse("replies", args=['10',]), data=data) # reply with id 4 doesn't exist
        reply = Replies.objects.get(pk =4)
        self.assertEqual(request.status_code,404)
        self.assertEqual(reply.text, "aaa")
    def test_reply_edit_fail_wrong_user(self):
        new_user =  User.objects.create_user(email="ss443@gmail.com",username="ssa6",password="asdefrfds")
        new_reply = Replies.objects.create(
            pk = 2,
            user = new_user,
            text="fsdf",
            parent_comment=self.cmnt,
            user_replying_to=new_user,
            movie_page=self.movie,
        )

        request = self.client.put(reverse("replies", args=['2']), {'text':'fsdkf'})
        self.assertEqual(request.status_code, 403)
    def test_reply_delete(self):
        reply = Replies.objects.create(
            pk = 6,
            user = self.user,
            text="aaa",
            parent_comment=self.cmnt,
            user_replying_to=self.user,
            movie_page=self.movie,
        )
    
        request = self.client.delete(reverse("replies", args=['6']))
        self.assertEqual(request.status_code , 200)
        self.assertIn("comments_count",request.json())
        self.assertEqual(request.json()["comments_count"],0)
        with self.assertRaises(ObjectDoesNotExist):
            Replies.objects.get(pk = 6)
    def test_reply_delete_fail_wrong_user(self):
        new_user = User.objects.create_user(email="ss3ssss@gmail.com",username="sssssa",password="asdessrfds")
        reply = Replies.objects.create(
                pk = 7,
                user = new_user,
                text="aaa",
                parent_comment=self.cmnt,
                user_replying_to=self.user,
                movie_page=self.movie,
            )
        request = self.client.delete(reverse("replies", args=['7']))
        self.assertEqual(request.status_code, 403)
        self.assertIsInstance(Replies.objects.get(pk = 7), Replies)
    def test_reply_delete_fail_doesnt_exist(self):
        request = self.client.delete(reverse("replies", args=['10'])) # no reply with id 10 
        self.assertEqual(request.status_code, 404)
    
