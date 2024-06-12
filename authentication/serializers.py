from .models import User
from rest_framework import serializers
from backend.settings import DOMAIN

class UserSerializer(serializers.ModelSerializer):
    pfp = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "username", "password","pfp")

    def get_pfp(self, obj):
        if obj.pfp:
            return DOMAIN + obj.pfp.url
        return None
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        fields = self.context.get('fields')

        if fields:
            return {field: data[field] for field in fields}
        
        return data