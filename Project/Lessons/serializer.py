from rest_framework import serializers
from .models import Lesson, Attendance, LessonTemplate
from Users.models import CustomUser
from Branches.models import Branch
from Groups.models import Group
from Students.models import Student
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError


class LessonsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'date', 'start_time', 'end_time', 'status', 'teacher', 'branch', 'student', 'group']


class AttendendanseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['id', 'lesson', 'student', 'present']


class LessonTemplateSerializer(serializers.ModelSerializer):
    strategy = serializers.ChoiceField(choices=['block', 'skip'], write_only=True, default='block')

    class Meta:
        model = LessonTemplate
        fields = [
            'id', 'branch', 'teacher', 'subject', 'student', 'group', 
            'days_of_week', 'start_time', 'end_time', 'start_date', 'end_date', 
            'is_active', 'strategy'
        ]


    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        student = data.get('student')
        group = data.get('group')
        subject = data.get('subject')

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {'end_date': 'end_date must be after start_date.'}
            )
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError(
                {'end_time': 'end_time must be after start_time.'}
            )
        if not student and not group:
            raise serializers.ValidationError(
                {'non_field_errors': 'A lesson template must have either a student or a group.'}
            )
        if subject and hasattr(subject, 'status') and subject.status == 'archived':
            raise serializers.ValidationError(
                {'subject': 'Cannot create a template with an archived subject.'}
            )
        return data


    def create(self, validated_data):
        strategy = validated_data.pop('strategy', 'block')
        
        try:
            template = super().create(validated_data)
            created_lessons, conflicts = template.generate_lessons(strategy=strategy)
            self.context['lessons_created_count'] = len(created_lessons)
            self.context['conflicts'] = conflicts
            
            
        except DjangoValidationError as e:
            if 'template' in locals():
                template.delete()
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))

        return template
