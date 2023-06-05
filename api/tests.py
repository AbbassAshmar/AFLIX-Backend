from django.test import TestCase,Client
from .models import *
from authentication.models import *
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from django.urls import reverse

def generate_movie(dir,title,imdb,imdbr,release,contentRate=None,genre=None):
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
        contentRate = contentRate if contentRate else "N/A",
        duration = 234,
        released = release,
        director= director
    )
    if genre is not None :
        for i in genre :
            g,created= Genre.objects.get_or_create(name=i)
            movie.genre.add(g)
    return movie

class Test_Favourite_View(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="ss@gmail.com",username="ssa",password="asderfds")
        cls.movie = generate_movie(dir="John Snow",title='movie1',imdb='fsdfewfwerew',imdbr='4' ,release='2024-04-04',genre=['Action'])
        cls.movie2 = generate_movie(dir="John2 Snow",title='movie2',imdb='fsdfe22wfwerew',imdbr='5',release='2024-04-04',genre=['Adventure'])
        cls.movie3 = generate_movie(dir="John2 Snow",title='movie3',imdb='jeiwjfoisjf',imdbr='9',release='2024-04-04')

    def setUp(self):
        token,created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+token.key)

    def test_favorite(self):
        fav = Favorite.objects.create(user=self.user,movie =self.movie)
        self.assertIsNotNone(fav)
    def test_get_favorite(self):
        fav = Favorite.objects.create(user=self.user,movie =self.movie)
        get_fav = Favorite.objects.get(user = self.user,movie=self.movie)
        self.assertEqual(fav,get_fav)
    def test_create_favorite(self):
        data = {
            "email":self.user.email,
            "movie_id":1
        }
        req = self.client.post(reverse("fav-create"),data=data)
        sreq = self.client.post(reverse("fav-create"),data=data)
        self.assertEqual(req.status_code,200)
        self.assertEqual(req.content,b'{"deleted/created":"created"}')
        self.assertEqual(sreq.content,b'{"deleted/created":"deleted"}')
    def test_retrieve_request_favorite(self):
        Favorite.objects.create(user=self.user, movie =self.movie)
        resp = self.client.get(reverse('fav-detail',args=[self.user.username,self.movie.pk]))
        resp2 = self.client.get(reverse('fav-detail',args=[self.user.username,'4948']))
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.content,b'{"found":true}')
        self.assertEqual(resp2.content,b'{"found":false}')

    def test_list_favourites(self):
        Favorite.objects.create(user=self.user,movie=self.movie)
        Favorite.objects.create(user=self.user,movie= self.movie2)
        request = self.client.get(reverse('fav-list',args=[self.user.pk]))
        self.assertEqual(request.status_code,200)
        self.assertEqual(request.json()['count'],2)
        movies_not_included = ['movie3']
        movies_included= [movie['title'] for movie in request.json()['movies']]
        for movie in movies_not_included :
            self.assertTrue(movie not in movies_included)

    def test_list_favourites_different_users(self):
        # user1 requesting the favourites of user2 
        user2 =User.objects.create_user(email="sfds@gmail.com",username="ssfdsa",password="asderfsdfds")
        request = self.client.get(reverse('fav-list',args=[user2.pk]))
        self.assertEqual(request.status_code,403)
        error = "Fobidden : You are not allowed to access the favorites of another user."
        self.assertEqual(request.json()['error'],error)

    def test_list_favourites_user_not_found(self):
        #user of id 39323 does not exist 
        request = self.client.get(reverse('fav-list',args=['39323']))
        self.assertEqual(request.status_code,404)
        error = "User does not exist"
        self.assertEqual(request.json()['error'],error)

    def test_list_favourites_no_favourites(self):
        user3 =User.objects.create_user(email="user3@gmail.com",username="user3",password="sfuewijor22")
        token2,created = Token.objects.get_or_create(user=user3)
        client2 = APIClient()
        client2.credentials(HTTP_AUTHORIZATION='Token '+token2.key)
        request = client2.get(reverse('fav-list',args=[user3.pk]))
        self.assertEqual(request.status_code, 200)
        self.assertEqual(request.json()['count'], 0)

    def test_list_favourites_user_not_authenticated(self):
        #no token associated with the request
        user4=User.objects.create_user(email="user4@gmail.com",username="user4",password="sfsdauewij22")
        client3 = APIClient()
        request = client3.get(reverse('fav-list',args=[user4.pk]))
        self.assertEqual(request.status_code , 401)
        self.assertEqual(request.json()['detail'], "Authentication credentials were not provided.")

    def test_list_favourites_with_limit(self):
        Favorite.objects.create(user=self.user,movie=self.movie)
        Favorite.objects.create(user=self.user,movie= self.movie2)
        request = self.client.get(reverse('fav-list',args=[self.user.pk]) +'?limit=1&start=0')
        self.assertEqual(request.status_code, 200)
        self.assertEqual(request.json()['count'], 1)
        self.assertEqual(request.json()['total_count'], 2)
        movies_not_included = ['movie3']
        movies_included= [movie['title'] for movie in request.json()['movies']]
        for movie in movies_not_included :
            self.assertTrue(movie not in movies_included)

    def test_list_favourites_with_filtering(self):
        Favorite.objects.create(user=self.user,movie=self.movie)
        Favorite.objects.create(user=self.user,movie= self.movie2)
        request = self.client.get(reverse('fav-list',args=[self.user.pk]) +'?genre=Action&released=2024')
        self.assertEqual(request.status_code, 200)
        self.assertEqual(request.json()['movies'][0]['title'], 'movie1')
        self.assertEqual(request.json()['count'], 1)
        
    
class Test_Movie_List_Api_View(TestCase):
    @classmethod
    def setUpTestData(cls) :
        cls.user = User.objects.create_user(email="email1@gmail.com",username="username",password="password")
        cls.movie1 = generate_movie("john","movie1","2432","7.2","2024-04-04",contentRate="R",genre=["Action","Adventure"])
        cls.movie2 = generate_movie("john1","movie2","232","7","2023-04-04",contentRate="G",genre=["Comedy","Adventure"])
        cls.movie3 = generate_movie("john2","movie3","242","6","2019-02-04",contentRate="G",genre=["Thriller","Sport"])
        cls.movie4 = generate_movie("terry","movie4","2452","9","2022-04-04",contentRate="PG",genre=["Action","Adventure"])
        cls.movie5 = generate_movie("tom2","movie5","24452","9","2025-04-04",contentRate="R+",genre=["Action","Sport"])
        cls.movie6 = generate_movie("terry","movie6","245442","2","2022-04-04",contentRate="PG",genre=["Drama","Adventure"])
        cls.movie7 = generate_movie("david","movie7","243222","9","2012-04-04",contentRate="R",genre=["Action","Adventure"])
        cls.movie8 = generate_movie("Fincher","movie8","244052","9","2009-04-04",contentRate="R",genre=["Comedy","thriller"])

    def setUp(self) :
        token, created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+token.key)

    def test_get_all_movies(self):
        request_all_movies = self.client.get(reverse("movie-list"))
        self.assertEqual(request_all_movies.status_code, 200)
        self.assertEqual(len(request_all_movies.json()["movies"]), 8)

    def test_get_movies_limited(self):
        request_movies_limit = self.client.get(reverse("movie-list")+"?start=0&limit=2")
        self.assertEqual(request_movies_limit.status_code, 200)
        self.assertEqual(len(request_movies_limit.json()["movies"]), 2)

    def test_get_movies_over_limit(self):
        request_movies_limit = self.client.get(reverse("movie-list")+"?limit=200")
        self.assertEqual(request_movies_limit.status_code, 200)
        self.assertEqual(len(request_movies_limit.json()["movies"]), 8)

    def test_get_movies_invlalid_limit(self):
        request_movies_limit = self.client.get(reverse("movie-list")+"?limit=string")
        self.assertEqual(request_movies_limit.status_code, 400)
        self.assertEqual(request_movies_limit.json()["error"], "invalid limit")

    def test_get_movies_filtered(self):
        request_movies = self.client.get(reverse("movie-list") +"?rated=R")
        self.assertEqual(request_movies.status_code , 200)
        self.assertEqual(len(request_movies.json()["movies"]),3)
        movies_to_be_included= ['movie1','movie7','movie8']
        self.assertTrue(movie.title in movies_to_be_included for movie in request_movies.json()['movies'])
    def test_get_movies_filtered_2(self):
        request_movies = self.client.get(reverse("movie-list") +"?genre=Action&genre=Adventure")
        self.assertEqual(request_movies.status_code , 200)
        self.assertEqual(len(request_movies.json()["movies"]),6)
        movies_to_be_included= ['movie1','movie2','movie4','movie5','movie6','movie7']
        self.assertTrue(movie.title in movies_to_be_included for movie in request_movies.json()['movies'])
    def test_get_movies_filtered_3(self):
        request_movies = self.client.get(reverse("movie-list") +"?rated=R&genre=Action&genre=Adventure")
        self.assertEqual(request_movies.status_code , 200)
        self.assertEqual(len(request_movies.json()["movies"]),2)
        movies_to_be_included= ['movie1','movie7']
        self.assertTrue(movie.title in movies_to_be_included for movie in request_movies.json()['movies'])
    def test_get_movies_filtered_4(self):
        request_movies = self.client.get(reverse("movie-list") +"?rated=All&genre=All&released=Unreleased")
        self.assertEqual(request_movies.status_code , 200)
        self.assertEqual(len(request_movies.json()["movies"]),2)
        movies_to_be_included= ['movie1','movie5']
        self.assertTrue(movie.title in movies_to_be_included for movie in request_movies.json()['movies'])
    def test_get_movies_filtered_5(self):
        request_movies = self.client.get(reverse("movie-list") +"?rated=All&genre=All&released=older")
        self.assertEqual(request_movies.status_code , 200)
        self.assertEqual(len(request_movies.json()["movies"]),2)
        movies_to_be_included= ['movie7','movie8']
        self.assertTrue(movie.title in movies_to_be_included for movie in request_movies.json()['movies'])
    def test_get_movies_filtered_limited(self):
        request_movies = self.client.get(reverse("movie-list") +"?genre=Action&genre=Adventure&start=0&limit=2")
        self.assertEqual(request_movies.status_code , 200)
        self.assertEqual(len(request_movies.json()["movies"]),2)
        movies_to_be_included= ['movie1','movie2',]
        self.assertTrue(movie.title in movies_to_be_included for movie in request_movies.json()['movies'])


class Test_Trending_Movie_Api_View(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="email1@gmail.com",username="username",password="password")
        cls.movie1 = generate_movie("john","movie1","2432","7.2","2024-04-04")
        cls.movie2 = generate_movie("john1","movie2","232","7","2023-04-04")
        cls.movie3 = generate_movie("john2","movie3","242","6","2023-02-04")
        cls.movie4 = generate_movie("terry","movie4","2452","9","2022-04-04")
        cls.movie5 = generate_movie("tom2","movie5","24452","9","2025-04-04")
        cls.movie6 = generate_movie("terry","movie6","245442","2","2022-04-04")
    def setUp(self) :
        self.token,created= Token.objects.get_or_create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+self.token.key)
    def test_get_trending_movies(self):
        request = self.client.get(reverse("movie-trending"))
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.json()['movies']), 2)
        names_list = [movie["title"] for movie in request.json()['movies']]
        self.assertEqual(names_list, ["movie2",'movie4'])
    def test_get_trending_movies_with_limit(self):
        request = self.client.get(reverse("movie-trending")+"?limit=1")
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.json()['movies']),1)
        names_list = [movie["title"] for movie in request.json()['movies']]
        self.assertEqual(names_list, ['movie2'])
    def test_get_trending_movies_with_invalid_limit(self):
        request = self.client.get(reverse("movie-trending")+"?limit=string")
        self.assertEqual(request.status_code, 400)
        self.assertEqual(request.json()["error"],"invalid limit")
    def test_get_trending_movies_with_over_limit(self):
        request = self.client.get(reverse("movie-trending")+"?limit=14") # 14 > len(movies)
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.json()['movies']),2) #if over limit , return all movies
        names_list = [movie["title"] for movie in request.json()['movies']]
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
        self.assertEqual(len(request.json()['movies']),4)
        for obj in request.json()['movies']:
            self.assertNotEqual(obj['title'] ,"movie1")
            self.assertNotEqual(obj['title'] ,"movie5")
    def test_get_latest_movies_with_limit(self):
        request = self.client.get(reverse("movie-latest")+"?limit=2")
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.json()['movies']),2)
        for obj in request.json()['movies']:
            self.assertNotEqual(obj['title'] ,"movie1")
            self.assertNotEqual(obj['title'] ,"movie5")
    def test_get_latest_movies_with_invalid_limit(self):
        request = self.client.get(reverse("movie-latest")+"?limit=string")
        self.assertEqual(request.status_code, 400)
        self.assertEqual(request.json()["error"],"invalid limit")
    def test_get_latest_movies_with_over_limit(self):
        request = self.client.get(reverse("movie-latest")+"?limit=15")
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.json()['movies']) , 4)
        for obj in request.json()['movies']:
            self.assertNotEqual(obj['title'] ,"movie1")
            self.assertNotEqual(obj['title'] ,"movie5")
    def test_get_latest_movies_with_0_or_negative_limit(self):
        request = self.client.get(reverse("movie-latest")+"?limit=0")
        self.assertEqual(request.status_code,400)
        self.assertEqual(request.json()["error"],"invalid limit")


class Test_Upcoming_Movie_Api_View(TestCase):
    @classmethod
    def setUpTestData(cls) :
        cls.user = User.objects.create_user(email="email1@gmail.com",username="username",password="password")
        cls.movie1 = generate_movie("john","movie1","2432",7.2,"2026-04-04")
        cls.movie2 = generate_movie("john1","movie2","232",7,"2029-05-07")
        cls.movie3 = generate_movie("john2","movie3","242",6,"2023-02-04")
        cls.movie4 = generate_movie("terry","movie4","2452",9,"1930-04-04")
        cls.movie5 = generate_movie("tom2","movie5","24452",9,"2025-04-04")
        cls.movie6 = generate_movie("terry","movie6","245442",2,"2040-04-04")
    def setUp(self):
        self.token,created= Token.objects.get_or_create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+self.token.key)
    def test_get_upcoming_movies(self):
        request = self.client.get(reverse("movie-upcoming"))
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.json()['movies']),4)
        for obj in request.json()['movies']:
            self.assertNotEqual(obj["title"],"movie3")
            self.assertNotEqual(obj["title"],"movie4")
    def test_get_upcoming_movies_with_limit(self):
        request = self.client.get(reverse("movie-upcoming")+"?limit=3")
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.json()['movies']),3)
        for obj in request.json()['movies']:
            self.assertNotEqual(obj["title"],"movie3")
            self.assertNotEqual(obj["title"],"movie4")
    def test_get_upcoming_movies_with_invalid_limit(self):
        request = self.client.get(reverse("movie-upcoming")+"?limit=string")
        self.assertEqual(request.status_code, 400)
        self.assertEqual(request.json()["error"],"invalid limit")
    def test_get_upcoming_movies_with_over_limit(self):
        request = self.client.get(reverse("movie-upcoming")+"?limit=200")
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.json()['movies']),4)
        for obj in request.json()['movies']:
            self.assertNotEqual(obj["title"],"movie3")
            self.assertNotEqual(obj["title"],"movie4")
    def test_get_upcoming_movies_with_0_or_negative_limit(self):
        request = self.client.get(reverse("movie-upcoming")+"?limit=0")
        self.assertEqual(request.status_code, 400)
        self.assertEqual(request.json()["error"],"invalid limit")

class Test_Similar_Movie_Api_View(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="email1@gmail.com",username="username",password="password")
        cls.movie1 = generate_movie("nolen","movie1","23123","8.1","2023-02-03",genre=["adventure", "action", "sport"])
        cls.movie2 = generate_movie("David Fincher","movie2","34344","10","2022-03-09",genre=["adventure", "thriller", "drama"])
        cls.movie3 = generate_movie("David Fincher","movie3","34654654","10","2014-03-09",genre=["comedey", "thriller", "drama"])
        cls.movie4 = generate_movie("martin scorsese","movie4","76123","5.5","2015-02-03",genre=["horror" , "science fiction"])
        cls.movie5 = generate_movie("tarantino","movie5","56123","8.1","2023-02-03",genre=["horror", "romance"])
        cls.movie6 = generate_movie("nolen","movie6","2314323","9.5","2021-02-03",genre=["animation"])
        cls.movie7 = generate_movie("nolen","movie7","2314423","4.1","2027-02-03",genre=["adventure", "documentary"])
        cls.movie8 = generate_movie("tarantino","movie8","2343123","5","2022-02-03",genre=["adventure", "comedey", "sport"])
        cls.movie9 = generate_movie("john","movie9","243123","5.3","2022-02-03",genre=["music"])
    def setUp(self) :
        self.token,created= Token.objects.get_or_create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+self.token.key)
    def test_get_similar_movies(self):
        request = self.client.get(reverse("movie-similar",kwargs={"id":self.movie1.pk}))
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.json()['movies']), 3)
        movies_response = [movie["title"] for movie in request.json()["movies"]]
        movies_included = ["movie2","movie8","movie6"]
        self.assertTrue(movie in movies_response for movie in movies_included)
    def test_get_similar_movies_movie4(self):
        request = self.client.get(reverse("movie-similar",kwargs={"id":self.movie4.pk}))
        self.assertEqual(request.status_code, 200)
        self.assertEqual(request.json()['movies'][0]["title"],"movie5")
    def test_get_similar_movies_id_doesnt_exist(self):
        request = self.client.get(reverse("movie-similar", kwargs={"id":3000}))
        self.assertEqual(request.status_code, 404)
        self.assertEqual(request.json()["error"],"movie does not exist")
    def test_get_similar_movies_no_similar_movies_found(self):
        request = self.client.get(reverse("movie-similar", kwargs={"id":self.movie9.pk}))
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.json()["movies"]) , 0)

class Test_Movies_Count_Api_View(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="email1@gmail.com",username="username",password="password")

        cls.movie1 = generate_movie("tarantino","movie1","2432",7.2,"2026-04-04")
        cls.movie2 = generate_movie("john","movie2","232",7,"2029-05-07")
        cls.movie3 = generate_movie("david","movie3","278432",7.2,"2026-04-04")

        cls.movie4 = generate_movie("locas","movie4","23432",6,"2022-05-07")
        cls.movie5 = generate_movie("bekker","movie5","5432",2,"2012-04-04")

        cls.movie6 = generate_movie("fincher","movie6","34453",7.9,"2023-05-07")
        cls.movie7 = generate_movie("david","movie7","22342",9,"2014-04-04")
        cls.movie8 = generate_movie("jonnathon","movie8","1232",7,"2020-05-07")
    def setUp(self) :
        self.token,created= Token.objects.get_or_create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+self.token.key)
    
    def test_get_movies_total_count(self):
        request = self.client.get(reverse("movies-count"))
        self.assertEqual(request.status_code, 200)
        self.assertEqual(request.json()['movies_count'], 8)

    def test_get_trending_movies_count(self):
        request = self.client.get(reverse('movies-count')+"?category=trending")
        self.assertEqual(request.status_code, 200)
        self.assertEqual(request.json()['movies_count'] ,3)

    def test_get_upcoming_movies_count(self):
        request = self.client.get(reverse('movies-count')+"?category=upcoming")
        self.assertEqual(request.status_code, 200)
        self.assertEqual(request.json()['movies_count'] ,3)
    def test_get_latest_movies_count(self):
        request = self.client.get(reverse('movies-count')+"?category=latest")
        self.assertEqual(request.status_code, 200)
        self.assertEqual(request.json()['movies_count'] ,5)

    def test_get_movies_count_invalid_category(self):
        request = self.client.get(reverse('movies-count')+"?category=anything")
        self.assertEqual(request.status_code, 400)
        self.assertEqual(request.json()['error'], "invalid category")
