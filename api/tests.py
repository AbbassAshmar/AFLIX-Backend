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

    # def test_Category_Id_Movies_view(self):
    #     client = Client(HTTP_AUTHORIZATION="Token "+self.token.key)
    #     resp = client.post(reverse("moviebycategory"),data={
    #         "id":1,
    #         "category":"Upcoming",
    #     })
    #     self.assertEqual(resp.status_code,200)
    #     self.assertIsNotNone(resp.content)


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
        self.assertEqual(request_movies_limit.json()["error"], "invalid limit")

def generate_movie(dir,title,imdb,imdbr,release,genre=None):
    director ,created= Directors.objects.get_or_create(name = dir)
    movie = Movie.objects.create(
        title = title,
        trailer = "www.aslkdfj",
        image = "www.fasd",
        thumbnail  = "www.ajskdf",
        imdbId = imdb,
        poster = "www.dfjsf",
        ratings={"imdb":imdbr,"metacritics":"N/A"},
        plot = "N/A",
        contentRate = "N/A",
        duration = 234,
        released = release,
        director= director
    )
    if genre is not None :
        for i in genre :
            g,created= Genre.objects.get_or_create(name=i)
            movie.genre.add(g)
    return movie

class Test_Trending_Movie_Api_View(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="email1@gmail.com",username="username",password="password")
        cls.movie1 = generate_movie("john","movie1","2432",7.2,"2024-04-04")
        cls.movie2 = generate_movie("john1","movie2","232",7,"2023-04-04")
        cls.movie3 = generate_movie("john2","movie3","242",6,"2023-02-04")
        cls.movie4 = generate_movie("terry","movie4","2452",9,"2022-04-04")
        cls.movie5 = generate_movie("tom2","movie5","24452",9,"2025-04-04")
        cls.movie6 = generate_movie("terry","movie6","245442",2,"2022-04-04")
    def setUp(self) :
        self.token,created= Token.objects.get_or_create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+self.token.key)
    def test_get_trending_movies(self):
        request = self.client.get(reverse("movie-trending"))
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.json()), 2)
        names_list = [movie["title"] for movie in request.json()]
        self.assertEqual(names_list, ["movie2",'movie4'])
    def test_get_trending_movies_with_limit(self):
        request = self.client.get(reverse("movie-trending")+"?limit=1")
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.json()),1)
        names_list = [movie["title"] for movie in request.json()]
        self.assertEqual(names_list, ['movie2'])
    def test_get_trending_movies_with_invalid_limit(self):
        request = self.client.get(reverse("movie-trending")+"?limit=string")
        self.assertEqual(request.status_code, 400)
        self.assertEqual(request.json()["error"],"invalid limit")
    def test_get_trending_movies_with_over_limit(self):
        request = self.client.get(reverse("movie-trending")+"?limit=14") # 14 > len(movies)
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.json()),2) #if over limit , return all movies
        names_list = [movie["title"] for movie in request.json()]
        self.assertEqual(names_list, ['movie2','movie4'])
    def test_get_trending_movies_with_0_or_negative_limit(self):
        request= self.client.get(reverse("movie-trending")+"?limit=0")
        self.assertEqual(request.status_code, 400)
        self.assertEqual(request.json()["error"],"invalid limit")

class Test_Latest_Movie_Api_View(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="email1@gmail.com",username="username",password="password")
        cls.movie1 = generate_movie("john","movie1","2432",7.2,"2024-04-04")
        cls.movie2 = generate_movie("john1","movie2","232",7,"2023-04-04")
        cls.movie3 = generate_movie("john2","movie3","242",6,"2023-02-04")
        cls.movie4 = generate_movie("terry","movie4","2452",9,"2022-04-04")
        cls.movie5 = generate_movie("tom2","movie5","24452",9,"2025-04-04")
        cls.movie6 = generate_movie("terry","movie6","245442",2,"2022-04-04")
    def setUp(self):
        self.token,created= Token.objects.get_or_create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+self.token.key)
    def test_get_latest_movies(self):
        request = self.client.get(reverse("movie-latest"))
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.json()),4)
        for obj in request.json():
            self.assertNotEqual(obj['title'] ,"movie1")
            self.assertNotEqual(obj['title'] ,"movie5")
    def test_get_latest_movies_with_limit(self):
        request = self.client.get(reverse("movie-latest")+"?limit=2")
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.json()),2)
        for obj in request.json():
            self.assertNotEqual(obj['title'] ,"movie1")
            self.assertNotEqual(obj['title'] ,"movie5")
    def test_get_latest_movies_with_invalid_limit(self):
        request = self.client.get(reverse("movie-latest")+"?limit=string")
        self.assertEqual(request.status_code, 400)
        self.assertEqual(request.json()["error"],"invalid limit")
    def test_get_latest_movies_with_over_limit(self):
        request = self.client.get(reverse("movie-latest")+"?limit=15")
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.json()) , 4)
        for obj in request.json():
            self.assertNotEqual(obj['title'] ,"movie1")
            self.assertNotEqual(obj['title'] ,"movie5")
    def test_get_latest_movies_with_0_or_negative_limit(self):
        request = self.client.get(reverse("movie-latest")+"?limit=0")
        self.assertEqual(request.status_code,400)
        self.assertEqual(request.json()["error"],"invalid limit")
