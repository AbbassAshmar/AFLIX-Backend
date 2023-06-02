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
        data["genre"]= [Genre.objects.get(pk=id).name for id in data['genre']]
        try :
            data["director"]= Directors.objects.get(pk=data["director"]).name
        except :
            data['director'] = None
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
            print(data["released"])
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

class FavouriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields ="__all__"