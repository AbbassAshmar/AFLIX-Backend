from rest_framework import serializers
from .models import Comments,Replies
from authentication.models import User

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comments
        fields = "__all__"
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["profile"]= User.objects.get(pk=data["user"]).pfp.url if  User.objects.get(pk=data["user"]).pfp else  User.objects.get(pk = data["user"]).username[0].upper()
        return data

class ReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Replies
        fields = "__all__"

    def to_representation(self,obj):
        data =  super().to_representation(obj)
        user2 = User.objects.get(pk = data["user_replying_to"]).username
        data["user_replying_to"]=user2
        data["profile"]= User.objects.get(pk=data["user"]).pfp.url if  User.objects.get(pk=data["user"]).pfp else User.objects.get(pk = data["user"]).username[0].upper()
        user = User.objects.get(pk = data["user"]).username
        data["user"]=user

        return data

class CommentReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Comments
        fields = "__all__"
    def to_representation(self, obj):
        data = super().to_representation(obj)
        user= User.objects.get(pk=data["user"]).username
        data["profile"]= User.objects.get(pk=data["user"]).pfp.url if  User.objects.get(pk=data["user"]).pfp else  User.objects.get(pk = data["user"]).username[0].upper()
        data["user"]= user
        replies = Replies.objects.filter(parent_comment = Comments.objects.get(pk=data["id"]))
        data["replies"] = ReplySerializer(replies, many=True).data
        return data
