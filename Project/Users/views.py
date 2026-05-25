from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login


from rest_framework import viewsets, permissions
from .models import CustomUser
from .serializers import CustomUserSerializer
from rest_framework.views import APIView

from rest_framework.response import Response
from rest_framework import status
from .permissions import IsAdminRole, IsTeacherRole
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class LoginView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, 'Project/login.html')
    
    def post(self, request):
        phone = request.data.get('phone')
        password = request.data.get('password')

        if not phone or not password:
            return Response({'error': 'Phone and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, phone=phone, password=password)
        if user and user.is_active:
            login(request, user)
            return redirect('home')
        return Response({'error': 'Phone or password is incorrect.'}, status=status.HTTP_401_UNAUTHORIZED)

class UserView(APIView):  # щоб отримати інформацію про користувача на сторінці
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        serializer = CustomUserSerializer(user)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAdminRole]

    @action(
        detail=False, 
        methods=['get', 'put', 'patch'], 
        permission_classes=[IsAuthenticated] # Перекриваємо глобальний IsAdminRole на звичайний IsAuthenticated (Слайд 45)
    )
    def me(self, request):
        user = request.user
        if request.method in ['PUT', 'PATCH']:
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        else:
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        
class CustomUserTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

   
