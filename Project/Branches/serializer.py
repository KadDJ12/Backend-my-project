from rest_framework import serializers
from .models import Branch, Subject

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'name', 'address', 'status', 'city']


class SubjectSerializer(serializers.ModelSerializer):
    branch = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Branch.objects.all()
    )
    
    class Meta:
        model = Subject
        fields = ['id', 'name', 'status', 'branch']