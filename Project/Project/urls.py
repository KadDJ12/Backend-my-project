"""
URL configuration for Project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from Users.views import LoginView, UserView, UserViewSet, CustomUserTokenObtainPairView
from Branches.views import BranchViewSet, SubjectViewSet

from django.urls import path, include
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularSwaggerView
from drf_spectacular.views import SpectacularAPIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import routers
from Users import views



router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'branches', BranchViewSet)  
router.register(r'subjects', SubjectViewSet)




urlpatterns = [ 
    path('admin/', admin.site.urls),
    path('login/', LoginView.as_view(), name='login'),
    path('home/', TemplateView.as_view(template_name='Project/home.html'), name='home'),
    
    path('', include(router.urls)),
    path('token/', CustomUserTokenObtainPairView.as_view(), name='token_obtain_pair'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    path('api/me/', UserView.as_view(), name='user_me'),


    path('api/branches/', BranchViewSet.as_view({'get': 'list', 'post': 'create'}), name='branch-list'),
    path('api/subjects/', SubjectViewSet.as_view({'get': 'list', 'post': 'create'}), name='subject-list'),
    
] 
