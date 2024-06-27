from .models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string
from custom_exceptions.custom_exceptions import NetworkError
import requests


class UserService :
    @staticmethod
    def register_user(data) :
        User.validate_register_required_fields(data)

        password = data["password"]
        confirm_password =data["confirm_password"]
       
        user = User(username= data['username'], email= data['email'], pfp=None)
        user.set_password(password)
        User.validate_passwords_match(password, confirm_password)
        
        user.save()
        return user
    
    @staticmethod
    def create_token(user) :
        Token.objects.filter(user = user).delete()
        return Token.objects.create(user = user)
    
    @staticmethod
    def get_user_with_email_password(email, password) :
        User.validate_login_required_fields({'email' : email, 'password' : password})

        try :
            user = User.objects.get(email = email)
        except ObjectDoesNotExist:
            raise ValidationError({"email" : "", "password" : "Account with this email does not exist!"})

        user.check_password_belongs_to_user(password)
        return user

    @staticmethod
    def update_user(user : User, new_data : object) : 
        updated_fields = []

        if new_data.get("new_password", None) : 
            required_fields = ['old_password', 'confirm_password'] 
            missing_fields = {field : f"{field.replace('_', ' ')} is Required" for field in required_fields if not new_data.get(field, "")}

            if missing_fields : 
                raise ValidationError(missing_fields)
            
            user.check_password_belongs_to_user(new_data['old_password'],'old_password')
            User.validate_passwords_match(new_data['new_password'], new_data['confirm_password'], 'new_password')

            user.set_password(new_data['new_password'], "new_password")
            updated_fields.append('password')

        if new_data.get('email', None) :
            user.email = new_data['email']
            updated_fields.append('email')

        if new_data.get('pfp' , None) :
            user.pfp.save(f"pfp_{user.pk}",new_data["pfp"]) 
            updated_fields.append('pfp')

        if new_data.get('username', None) : 
            user.username = new_data['username']
            updated_fields.append('username')

        user.save(update_fields=updated_fields)
        return user
    
class GoogleAuthService :
    token_info_url = "https://www.googleapis.com/oauth2/v3/tokeninfo"
    owner_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"

    def __init__(self, access_token, client_id) : 
        self.access_token = access_token
        self.client_id = client_id
        self.token_details = {}
        self.owner_details = {}

    def fetch_access_token_details(self) : 
        url = f"{GoogleAuthService.token_info_url}?access_token={self.access_token}"
        try:
            response = requests.get(url, timeout=5) 
            response.raise_for_status() #if status code is an error raise exception
            self.token_details = response.json()
        except requests.exceptions.RequestException as e:
            raise NetworkError("Error fetching token details") 

    def fetch_access_token_owner_details(self) : 
        url = f"{GoogleAuthService.owner_info_url}?access_token={self.access_token}"
        try:
            response = requests.get(url, timeout=5) 
            response.raise_for_status()  
            self.owner_details = response.json()
        except requests.exceptions.RequestException as e:
            raise NetworkError("Error fetching user details") 
        
    def validate_google_access_token(self,token_details, owner_details) :
        if int(token_details["expires_in"]) <= 0 :
            raise ValidationError({"message" : "Access token expired."})
        
        #the token should be for this server, aud is the server unique id.
        if token_details["aud"] != self.client_id :
            raise ValidationError({"message" : "Access token is not valid."})
        
        #creator of the token is the same as
        if token_details["sub"] != owner_details["sub"]: 
            raise ValidationError({"message" : "Access token does not belong to this user."})

        return True
    
    def authenticate_user(self) :
        self.fetch_access_token_details()
        self.fetch_access_token_owner_details()

        is_valid = self.validate_google_access_token(self.token_details, self.owner_details)

        if is_valid : 
            data = {
                "email":self.owner_details["email"], 
                "username":self.owner_details["name"], 
                "password" : GoogleAuthService.get_random_password(),
                "pfp" : self.owner_details['picture']
            }
            
            user = User.objects.filter(email = data['email']).first()
            if not user: 
                user =  User.objects.create(**data)
            
            return user
        
        return User.objects.none()
    
    @staticmethod
    def get_random_password():
        return get_random_string(20)
    



