from .models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist

class UserService :
    @staticmethod
    def create_user(data) :
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
        updated_fields = {}

        if new_data.get("new_password", None) : 
            required_fields = ['old_password', 'confirm_password'] 
            missing_fields = {field : f"{field.replace('_', ' ')} is Required" for field in required_fields if not new_data.get(field, "")}

            if missing_fields : 
                raise ValidationError(missing_fields)
            
            user.check_password_belongs_to_user(new_data['old_password'],'old_password')
            User.validate_passwords_match(new_data['new_password'], new_data['confirm_password'], 'new_password')

            user.set_password(new_data['new_password'], "new_password")
            updated_fields["password"] = user.password

        if new_data.get('email', None) :
            user.email = new_data['email']
            updated_fields["email"] = user.email

        if new_data.get('pfp' , None) :
            user.pfp.save('pfp.jpg',new_data["pfp"])   
            updated_fields["pfp"] = user.pfp.url

        if new_data.get('username', None) : 
            user.username = new_data['username']
            updated_fields["username"] = user.username 

        user.save(update_fields=[field for field in updated_fields])
        return user



