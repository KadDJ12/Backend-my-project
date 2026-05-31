from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate
from Branches.models import Branch





class CustomUserSerializer(serializers.ModelSerializer):
    branches = serializers.SlugRelatedField( # щоб відображалося імя філії а не її айді 
        many=True,
        read_only = True,
        slug_field='name' 
    )
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'phone', 'role', 'registered_at', 'password','branches']
        extra_kwargs = {
            'password': {'write_only': True}
        }


    def create(self, validated_data):
        branches_data = validated_data.pop('branches', None)
        user = CustomUser.objects.create_user(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data['phone'],
            password=validated_data['password'],
            role=validated_data.get('role', 'teacher'),
            branches=validated_data.get('branches')
        )
        if branches_data is not None:
            user.branches.set(branches_data)
        return user
    
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
            instance.save()
        return super().update(instance, validated_data)
    
    
    

class UserReadSerializer(serializers.ModelSerializer):
    branches = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name' 
    )
    
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'phone', 'role', 'registered_at', 'branches']
        extra_kwargs = {
            'branches': {'read_only': True},
            'role': {'read_only': True},
            'id': {'read_only': True},
        }
        
        
        
        
class MeUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'password']        
  
  
  
  
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'role', 'branches']
        extra_kwargs = {
            'phone': {'read_only': True}
        }

    
    
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'phone' 
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['phone'] = user.phone
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['role'] = getattr(user, 'role', 'teacher')
        return token


    def validate(self, attrs):
        phone = attrs.get('phone')
        password = attrs.get('password')
        error_message = "Невірна комбінація телефону та паролю або акаунт деактивовано."
        user = authenticate(request=self.context.get('request'), phone=phone, password=password)
        if user is None:
            raise AuthenticationFailed(error_message, code='authentication_failed')
        if not user.is_active:
            raise AuthenticationFailed(error_message, code='authentication_failed')
        attrs['username'] = phone
        data = super().validate(attrs)
        data['user'] = UserReadSerializer(user).data
        return data
    
    
    

