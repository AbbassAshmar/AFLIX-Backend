from django.test import TestCase,Client
from .models import *
from authentication.models import *
from rest_framework.authtoken.models import Token
from django.urls import reverse

class Test_Favourite_View(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="ss@gmail.com",username="ssa",password="asderfds")
        cls.token,created = Token.objects.get_or_create(user = cls.user)
        cls.movie = Movie.objects.create(title="iew",
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
           
    def test_favorite(self):
        fav = Favorite.objects.create(user=self.user,movie =self.movie)
        self.assertIsNotNone(fav)
    def test_get_favorite(self):
        fav = Favorite.objects.create(user=self.user,movie =self.movie)
        get_fav = Favorite.objects.get(user = self.user,movie=self.movie)
        self.assertEqual(fav,get_fav)
    def test_post_request_favorite(self):
        data = {
            "email":self.user.email,
            "movie_id":1
        }
        client = Client(HTTP_AUTHORIZATION='Token ' + self.token.key)
        req = client.post(reverse("fav-create"),data=data)
        sreq = client.post(reverse("fav-create"),data=data)
        self.assertEqual(req.status_code,200)
        self.assertEqual(req.content,b'{"deleted/created":"created"}')
        self.assertEqual(sreq.content,b'{"deleted/created":"delete"}')
    def test_retrieve_request_favorite(self):
        client = Client(HTTP_AUTHORIZATION='Token ' + self.token.key)
        data = {
            "email":self.user.email,
            "movie_id":1
        }
        client.post(reverse("fav-create"),data=data)
        resp = client.get(reverse('fav-detail',args=["ssa","1"]))
        resp2 = client.get(reverse('fav-detail',args=['ssa','2']))
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.content,b'{"found":true}')
        self.assertEqual(resp2.content,b'{"found":false}')

    def test_Category_Id_Movies_view(self):
        client = Client(HTTP_AUTHORIZATION="Token "+self.token.key)
        resp = client.post(reverse("moviebycategory"),data={
            "id":1,
            "category":"Upcoming",
        })
        self.assertEqual(resp.status_code,200)
        self.assertIsNotNone(resp.content)