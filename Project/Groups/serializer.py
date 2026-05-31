from rest_framework import serializers
from .models import Group
from Branches.models import Branch
from Students.models import Student

class GroupSerializer(serializers.ModelSerializer):
    branch = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Branch.objects.all()
    )
    class Meta():
        model = Group
        fields = ['name','status','branch','students','id']



