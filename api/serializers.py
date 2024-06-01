from rest_framework import serializers
from .models import *
from datetime import datetime, date
from django.core.exceptions import ValidationError

class MoviesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = "__all__"

    def to_representation(self, obj):
        # transforms internal representation (model instance) to external representation like dictionaty.
        data = super().to_representation(obj)

        base_url = "http://image.tmdb.org/t/p/"
        poster_size = "w342"
        image_size= "w300"

        if not data['image']  :
            data['image'] = "https://imdb-api.com/images/128x176/nopicture.jpg"
        
        if not data['poster'] :
            data['poster'] = "https://imdb-api.com/images/128x176/nopicture.jpg"

        if data['image'].split("/")[-1] != "nopicture.jpg" : 
            data['image'] = base_url + image_size + "/" + data['image']

        if data['poster'].split("/")[-1] != "nopicture.jpg" : 
            data['poster'] =  base_url + poster_size + "/" + data['poster']

        if data['trailer'] :
            data['trailer'] = f"https://www.youtube.com/watch?v={data['trailer']}"

        data["genre"]= [Genre.objects.get(pk=id).name for id in data['genre']]
        data['director'] = DirectorsSerializer(Directors.objects.filter(pk=data['director']).first()).data

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
  
class DirectorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Directors
        fields ="__all__"

class GenresSerializer(serializers.ModelSerializer):
    class Meta:
        model= Genre
        fields ="__all__"

class ContentRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model= ContentRating
        fields ="__all__"



    