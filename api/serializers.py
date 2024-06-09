from rest_framework import serializers
from .models import *
from datetime import datetime, date
from django.core.exceptions import ValidationError

class DirectorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Directors
        fields ="__all__"

class GenresSerializer(serializers.ModelSerializer):
    class Meta:
        model= Genre
        fields ="__all__"

class MoviesSerializer(serializers.ModelSerializer):
    genres = GenresSerializer(many=True, read_only=True)
    director = DirectorsSerializer()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = "__all__"

    def get_is_favorite(self, obj):
            user = None
            request = self.context.get("request")
           
            if request and hasattr(request, "user"):
                user = request.user

            if user and user.is_authenticated :
                return user.favorites.filter(movie=obj).exists()
            
            return False

    def to_representation(self, obj):
        # transforms internal representation (model instance) to external representation like dictionaty.
        data = super().to_representation(obj)

        base_url = "http://image.tmdb.org/t/p/"
        poster_size = "w342" # w92,w154,w185,w342,w500,w780,original
        image_size= "w1280" # w780, w1280 , w300 , original

        if not data['image']  :
            data['image'] = "https://imdb-api.com/images/128x176/nopicture.jpg"
        
        if not data['poster'] :
            data['poster'] = "https://imdb-api.com/images/128x176/nopicture.jpg"

        if data['image'] and data['image'].split("/")[-1] != "nopicture.jpg" : 
            data['image'] = base_url + image_size + "/" + data['image']

        if data['poster'].split("/")[-1] != "nopicture.jpg" : 
            data['poster'] =  base_url + poster_size + "/" + data['poster']

        if data['trailer'] :
            data['trailer'] = f"https://www.youtube.com/embed/{data['trailer']}"

        return data
    
    def to_internal_value(self, data): #executed during is_valid(), transforms any format (ex.json) to python respresentation (ex.dic).
        # the representation is saved in the database after the serializer calls update or create methods and passing the trans data.
        try: 
            try: 
                releasedd= datetime.strptime(data["released"].replace(",",""),"%d %b %Y")
            except :
                releasedd = datetime.strptime(data["released"].replace(",",""),"%b %d %Y")
            releasedd = releasedd.date()
            data["released"] = releasedd
        except ValueError:
            data['released'] = None
        return super().to_internal_value(data)
  

class ContentRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model= ContentRating
        fields ="__all__"



    