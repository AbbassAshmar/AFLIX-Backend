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
    
