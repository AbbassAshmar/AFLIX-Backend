from django.test import TestCase
from api.models import Movie, Directors, Genre
from rest_framework.authtoken.models import Token
from authentication.models import User, Comments, Replies
from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from .views import CommentApiView
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



# class Test_Replies(TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         cls.user = User.objects.create_user(email="ss3@gmail.com",username="ssa",password="asderfds")
#         cls.movie = Movie.objects.create(
#         pk=1,
#         title="iew",
#         trailer="www.sdiojfdsijfiejwfijwoifj",
#         image="www.sdiojfdsijfiejwfijwoifj",
#         thumbnail="www.sdiojfdsijfiejwfijwoifj",
#         imdbId='fsdfewfwerew',
#         poster="www.sdiojfdsijfiejwfijwoifj",
#         ratings={"imdb":"N/A","metacritics":"N/A"},
#         plot="N/A",
#         contentRate="N/A",
#         duration=234,
#         released="2024-04-04",
#         director=Directors.objects.create(name="John Snow"))
#         cls.cmnt = Comments.objects.create(pk=1,user=cls.user,
#         profile = cls.user,
#         movie_page=cls.movie,
#         text="anidfjo",)
#         cls.cmnt.user_ld.add(cls.user)
#     def setUp(self):
#         self.token ,created= Token.objects.get_or_create(user = self.user)
#         self.client = APIClient()
#         self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
#     def test_reply_create(self):
#         data = {
#            'text' :"aadifj",
#            'parent-comment-id':"1",
#            "username_replying_to":"ssa",
#            "dateAdded":'2023-03-25T15:07:54Z',
#            "page_id":'1'
#         }
#         request = self.client.post(reverse('replies'), data=data)
#         self.assertEqual(request.status_code, 200)
#         reply = Replies.objects.get(pk=2)
#         self.assertIsInstance(reply, Replies)
#         self.assertEqual(request.json()['comments_count'] , 1)
#         self.assertEqual(reply.parent_comment.pk,1)
#     def test_reply_create_fail_user_fail(self):
        
#         data={
#             'text':"fwiefj",
#             'parent-comment-id':"1",
#             "username_replying_to":"ssfijeowa",#user doesn't exist
#             "dateAdded":'2023-03-25T15:07:54Z',
#             "page_id":'1'
#         }
#         with self.assertRaises(ObjectDoesNotExist):
#             request = self.client.post(reverse('replies'), data = data)
#     def test_reply_create_fail_comment_fail(self):
#         data={
#             'text':"fwiefj",
#             'parent-comment-id':"5",#comment doesn't exist
#             "username_replying_to":"ssa",
#             "dateAdded":'2023-03-25T15:07:54Z',
#             "page_id":'1'
#         }
#         with self.assertRaises(ObjectDoesNotExist):
#             request = self.client.post(reverse('replies'), data = data)
#     def test_reply_create_fail_page_id_fail(self):
#         data={
#             'text':"fwiefj",
#             'parent-comment-id':"1",
#             "username_replying_to":"ssa",
#             "dateAdded":'2023-03-25T15:07:54Z',
#             "page_id":'6'#page id doesn't exist
#         }
#         with self.assertRaises(ObjectDoesNotExist):
#             request = self.client.post(reverse('replies'), data = data)    
#     def test_reply_edit(self):
#         data = {
#            'text' :"aaa",
#            'parent-comment-id':"1",
#            "username_replying_to":"ssa",
#            "dateAdded":'2023-03-25T15:07:54Z',
#            "page_id":'1'
#         }
#         request = self.client.post(reverse('replies'), data=data)
#         reply = Replies.objects.get(pk =1)
#         self.assertEqual(reply.text,"aaa")
#         data={
#             'text':"bbb",
#         }
#         request = self.client.put(reverse("replies", args=['1',]), data=data)
#         self.assertEqual(request.status_code, 200)
#         expected_response_keys = ["text", ""]
#         self.assertIn(request.json(),)
#         self.assertDictEqual(request.json(),)
#         reply = Replies.objects.get(pk =1)
#         self.assertEqual(reply.text, "bbb")
#     def text_reply_edit_fail(self):
#         data = {
#            'text' :"aaa",
#            'parent-comment-id':"1",
#            "username_replying_to":"ssa",
#            "dateAdded":'2023-03-25T15:07:54Z',
#            "page_id":'1'
#         }
#         request = self.client.post(reverse('replies'), data=data)
#         reply = Replies.objects.get(pk =1)
#         self.assertEqual(reply.text,"aaa")
#         data={
#             'text':"",
#         }
#         request = self.client.put(reverse("replies", args=['1',]), data=data)
#         self.assertEqual(request.status_code, 400)
#         reply = Replies.objects.get(pk =1)
#         self.assertEqual(request.json()['error'], "no text provided")
#         self.assertEqual(reply.text, "aaa")
#     def test_reply_edit_doesnt_exist(self):
#         data = {
#            'text' :"aaa",
#            'parent-comment-id':"1",
#            "username_replying_to":"ssa",
#            "dateAdded":'2023-03-25T15:07:54Z',
#            "page_id":'1'
#         }
#         request = self.client.post(reverse('replies'), data=data)
#         reply = Replies.objects.get(pk =1)
#         self.assertEqual(reply.text,"aaa")
#         data = {
#             'text':"bbb",
#         }
#         request = self.client.put(reverse("replies", args=['4',]), data=data) # reply with id 4 doesn't exist
#         reply = Replies.objects.get(pk =1)
#         self.assertEqual(request.status_code,404)
#         self.assertEqual(request.json()['error'], "reply doesn't exist")
#         self.assertEqual(reply.text, "aaa")

#     def test_reply_delete(self):
#         pass
    
