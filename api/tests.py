from django.test import TestCase,Client
from .models import *
from authentication.models import *
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
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

class Test_Movies_List_Api_View(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="email1@gmail.com",username="username",password="password")
        cls.movie1 = Movie.objects.create(
        title="movie1",
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

        cls.movie2 = Movie.objects.create(
        title="movie2",
        trailer="www.sdiojfdsijfiejwfijwoifj",
        image="www.sdiojfdsijfiejwfijwoifj",
        thumbnail="www.sdiojfdsijfiejwfijwoifj",
        imdbId='fsdfewfwlerew',
        poster="www.sdiojfdsijfiejwfijwoifj",
        ratings={"imdb":"N/A","metacritics":"N/A"},
        plot="N/A",
        contentRate="N/A",
        duration=234,
        released="2024-04-04",
        director=Directors.objects.create(name="John Snow2"))

        cls.movie3 = Movie.objects.create(
        title="movie3",
        trailer="www.sdiojfdsijfiejwfijwoifj",
        image="www.sdiojfdsijfiejwfijwoifj",
        thumbnail="www.sdiojfdsijfiejwfijwoifj",
        imdbId='fsdfewfwereiw',
        poster="www.sdiojfdsijfiejwfijwoifj",
        ratings={"imdb":"N/A","metacritics":"N/A"},
        plot="N/A",
        contentRate="N/A",
        duration=234,
        released="2024-04-04",
        director=Directors.objects.create(name="John Snow3"))
    def setUp(self):
        self.token, created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+self.token.key)

    def test_list_all_movies(self):
        request_all_movies = self.client.get(reverse("movie-list"))
        print("___________________________________--")
        self.assertEqual(request_all_movies.status_code, 200)
        self.assertEqual(len(request_all_movies.json()["movies"]), 3)
    def test_list_all_movies_with_limit(self):
        request_movies_limit = self.client.get(reverse("movie-list")+"?limit=2")
        self.assertEqual(request_movies_limit.status_code, 200)
        self.assertEqual(len(request_movies_limit.json()["movies"]), 2)
    def test_list_all_movies_with_over_limit(self):
        request_movies_limit = self.client.get(reverse("movie-list")+"?limit=4")
        self.assertEqual(request_movies_limit.status_code, 200)
        self.assertEqual(len(request_movies_limit.json()["movies"]), 3)
    def test_list_all_movies_with_invalid_limit(self):
        request_movies_limit = self.client.get(reverse("movie-list")+"?limit=string")
        self.assertEqual(request_movies_limit.status_code, 400)
        self.assertEqual(len(request_movies_limit.json()["error"]), "invalid limit")


