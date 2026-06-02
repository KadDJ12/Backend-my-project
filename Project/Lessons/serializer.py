from rest_framework import serializers
from .models import Lesson, Attendance
from Users.models import CustomUser
from Branches.models import Branch
from Groups.models import Group
from Students.models import Student


class LessonsSerializer(serializers.ModelSerializer):
    teacher = serializers.SlugRelatedField(slug_field='first_name', queryset=CustomUser.objects.filter(role='teacher'))
    branch = serializers.SlugRelatedField(slug_field='name', queryset=Branch.objects.all())
    group = serializers.SlugRelatedField(slug_field='name', queryset=Group.objects.all())

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'date', 'start_time', 'end_time', 'status', 'teacher', 'branch', 'group']


class AttendendanseSerializer(serializers.ModelSerializer):
    student = serializers.SlugRelatedField(slug_field='first_name', queryset=Student.objects.all())
    lesson = serializers.SlugRelatedField(slug_field='title', queryset=Lesson.objects.all())

    class Meta:
        model = Attendance
        fields = ['id', 'lesson', 'student', 'present']