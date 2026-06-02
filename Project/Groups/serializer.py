from rest_framework import serializers
from .models import Group
from Branches.models import Branch

class GroupSerializer(serializers.ModelSerializer):
    branch = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Branch.objects.all()
    )
    students = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'status', 'branch', 'students']



