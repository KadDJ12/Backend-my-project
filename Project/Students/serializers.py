from rest_framework import serializers
from .models import Student
from rest_framework.permissions import IsAuthenticated
from Users.permissions import IsAdminOrTeacherRole
from Branches.models import Branch


class StudentSerializer(serializers.ModelSerializer):
    branch = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Branch.objects.all()
    )
    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'registered_at', 'home_address', 'parent_nuber', 'status', 'branch']

        
