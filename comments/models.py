from django.db import models
from authentication.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Base(models.Model):
    text = models.TextField(blank=False,editable=True)
    created_at = models.DateTimeField(editable=True,null=True,blank=True)

    def __str__(self):
        return self.user.username + ":" + self.text

    class Meta:
        abstract = True

class Comment(Base):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments",null=False)
    movie = models.ForeignKey("api.Movie",related_name="comments", on_delete=models.CASCADE,null=False)
    likes_dislikes = models.ManyToManyField(User, through="CommentLikeDislike")

    @property
    def likes_count(self) :
        return self.likes_dislikes.through.objects.filter(comment = self, interaction_type=1).count()

    @property
    def dislikes_count(self) :
        return self.likes_dislikes.through.objects.filter(comment = self, interaction_type=2).count()

class Reply(Base):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="replies",null=False)
    movie = models.ForeignKey("api.Movie",on_delete=models.CASCADE,related_name="replies",null=False)
    parent_comment = models.ForeignKey(Comment, on_delete=models.CASCADE,related_name="replies",null=False)
    replying_to = models.ForeignKey("self",on_delete=models.CASCADE,related_name="replied_to_me",null=True,blank=True)
    likes_dislikes = models.ManyToManyField(User, through="ReplyLikeDislike")

    @property
    def likes_count(self) :
        return self.likes_dislikes.through.objects.filter(reply = self, interaction_type=1).count()

    @property
    def dislikes_count(self) :
        return self.likes_dislikes.through.objects.filter(reply = self, interaction_type=2).count()

class CommentLikeDislike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    interaction_type = models.IntegerField(default=0,null=False,validators=[MinValueValidator(0),MaxValueValidator(2)])

class ReplyLikeDislike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE)
    interaction_type = models.IntegerField(default=0,null=False,validators=[MinValueValidator(0),MaxValueValidator(2)])
    # 0-> no like or dislike , 1->like, 2->dislike