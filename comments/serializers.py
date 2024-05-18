from rest_framework import serializers
from .models import Comment,Reply, CommentLikeDislike
from authentication.models import User
from authentication.serializers import UserSerializer

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"

    def get_likes(self, obj):
        return CommentLikeDislike.objects.filter(comment=obj, interaction_type=1).count()

    def get_dislikes(self, obj):
        return CommentLikeDislike.objects.filter(comment=obj, interaction_type=2).count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["user"]= UserSerializer(instance.user).data
        data["replies"] = ReplySerializer(instance.replies.all(),many=True).data
        return data

class ReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Reply
        fields = "__all__"

    def get_likes(self, obj):
        return CommentLikeDislike.objects.filter(reply=obj, interaction_type=1).count()

    def get_dislikes(self, obj):
        return CommentLikeDislike.objects.filter(reply=obj, interaction_type=2).count()

    def to_representation(self,instance):
        data = super().to_representation(instance)
        data["user"] = UserSerializer(instance.user).data
        data['replying_to'] = {
            "text" : instance.replying_to.text,
            "movie" : instance.replying_to.movie.id,
            "user" : UserSerializer(instance.replying_to.user),
            "likes": CommentLikeDislike.objects.filter(reply=instance.replying_to, interaction_type=1).count(),
            "dislikes": CommentLikeDislike.objects.filter(reply=instance.replying_to, interaction_type=2).count(),
            "parent_comment" : instance.replying_to.parent_comment,
            "created_at" : instance.replying_to.created_at
        }
        
        return data

