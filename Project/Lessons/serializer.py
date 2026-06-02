from rest_framework import serializers
from .models import Lesson, Attendance,LessonTemplate
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




class LessonTemplateSerializer(serializers.ModelSerializer):
    teacher_name = serializers.ReadOnlyField(source='teacher.first_name')
    branch_name = serializers.ReadOnlyField(source='branch.name')
    group_name = serializers.ReadOnlyField(source='group.name')
    student_name = serializers.ReadOnlyField(source='student.first_name')

    class Meta:
        model = LessonTemplate
        fields = [
            'id', 'branch', 'branch_name', 'teacher', 'teacher_name', 
            'subject', 'student', 'student_name', 'group', 'group_name', 
            'days_of_week', 'start_time', 'end_time', 'start_date', 'end_date', 'is_active'
        ]

    def validate(self, attrs):
        # Додаткова перевірка на рівні серіалізатора (про всяк випадок)
        if attrs.get('start_date') > attrs.get('end_date'):
            raise serializers.ValidationError({"start_date": "Дата початку не може бути більшою за дату закінчення."})
        return attrs


