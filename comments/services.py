
from helpers.get_object_or_404 import get_object_or_404
from rest_framework.request import Request

class LikeDislikeService:
    def __init__(self, model, like_dislike_model):
        self.model = model
        self.like_dislike_model = like_dislike_model

    def like(self, request : Request, pk : int) :
        user, model_instance = self.get_user_and_model(request, pk)
        like_dislike_model, created = self.like_dislike_model.objects.get_or_create(user= user,**{self.model.__name__.lower(): model_instance})
      
        if not created and like_dislike_model.interaction_type == 1 :
            self.remove_interaction(like_dislike_model)
            action = 'like removed'
        else : 
            self.set_like(like_dislike_model)
            action = 'like added'
        
        return {'action' : action , 'likes_count': model_instance.likes_count, 'dislikes_count' :  model_instance.dislikes_count }
        
    def dislike(self, request : Request, pk : int) : 
        user, model_instance = self.get_user_and_model(request, pk)
        like_dislike_model, created = self.like_dislike_model.objects.get_or_create(user= user,**{self.model.__name__.lower(): model_instance})
      
        if not created and like_dislike_model.interaction_type == 2 : #remove the like 1->0
            self.remove_interaction(like_dislike_model)
            action ='dislike removed'
        else : 
            self.set_dislike(like_dislike_model)
            action ='dislike added'
        
        return {'action' : action , 'likes_count': model_instance.likes_count, 'dislikes_count' :  model_instance.dislikes_count }
    
    def get_user_and_model(self, request, pk) :
        user = request.user
        model_instance = get_object_or_404(self.model, pk , f"{self.model.__name__} not found.")
        return [user, model_instance]
    
    def remove_interaction(self,like_dislike_model) :
        like_dislike_model.interaction_type = 0
        like_dislike_model.save(update_fields=['interaction_type'])

    def set_dislike(self,like_dislike_model): 
        like_dislike_model.interaction_type = 2
        like_dislike_model.save(update_fields=['interaction_type'])

    def set_like(self,like_dislike_model): 
        like_dislike_model.interaction_type = 1
        like_dislike_model.save(update_fields=['interaction_type'])
        