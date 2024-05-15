from .models import User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "username", "password","pfp")



# 1- The to_representation method of serializers.ModelSerializer converts the fields of the model instance into a dictionary representation.
# 2- A custom to_representation method can be used to further modify the dictionary representation if necessary.
# 3- The Django Rest Framework converts the dictionary representation into JSON or another content type for the final representation of the data in the HTTP response.