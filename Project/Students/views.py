from django.shortcuts import render
from .serializers import StudentSerializer
from rest_framework import viewsets,status
from rest_framework.decorators import action
from Users.permissions import IsAdminOrTeacherRole
from rest_framework.permissions import IsAuthenticated
from .models import Student
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action






class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrTeacherRole,IsAuthenticated]
    filter_backends = [DjangoFilterBackend,SearchFilter]
    search_fields = ['first_name', 'last_name','id']


    def get_queryset(self):
        user = self.request.user
        if not user or user.is_anonymous:
            return Student.objects.none()

        if user.is_superuser:
            return Student.objects.all()

        if user.role == 'teacher':
            from Lessons.models import Lesson
            from django.db.models import Q
            student_ids = Lesson.objects.filter(teacher=user).values_list('student_id', flat=True)
            group_ids = Lesson.objects.filter(teacher=user, group__isnull=False).values_list('group_id', flat=True)
            return Student.objects.filter(
                Q(id__in=student_ids) | Q(groups__id__in=group_ids),
                status='active'
            ).distinct()

        return Student.objects.filter(
            branch__in=user.branches.all(),
            status='active').distinct()

    
    def check_permissions(self, request):
        super().check_permissions(request)

        if request.user.role == 'teacher' and request.method not in ['GET', 'HEAD', 'OPTIONS']:
            self.permission_denied(
                request,
                message='Teacher is not allowed to create or edit students'
            )


    def destroy(self, request, *args, **kwargs):

        student = self.get_object()
        student.status = 'archived'
        student.save()

        return Response(
            {
                'message': f'Студента {student.first_name} {student.last_name} переведено в статус Archived.'
            }, 
            status=status.HTTP_200_OK
        )


    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsAdminOrTeacherRole])
    def attendance_history(self, request, pk=None):
        student = self.get_object()
        subject_id = request.query_params.get('subject_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        queryset = student.attendances.all()

        if subject_id:
            queryset = queryset.filter(lesson__subject_id=subject_id)
        if start_date:
            queryset = queryset.filter(lesson__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(lesson__date__lte=end_date)
            
        user = request.user
        if user.role == 'teacher':
            queryset = queryset.filter(lesson__teacher=user)

        total_lessons = queryset.count()
        attended_lessons = queryset.filter(present=True).count()
        missed_lessons = total_lessons - attended_lessons
        attendance_percentage = (attended_lessons / total_lessons * 100) if total_lessons > 0 else 0
        records = []
        for att in queryset.select_related('lesson', 'lesson__subject', 'lesson__teacher'):
            records.append({
                'id': att.id,
                'lesson': {
                    'id': att.lesson.id,
                    'title': att.lesson.title,
                    'date': att.lesson.date.strftime('%Y-%m-%d'),
                    'start_time': att.lesson.start_time.strftime('%H:%M:%S'),
                    'end_time': att.lesson.end_time.strftime('%H:%M:%S'),
                    'subject': att.lesson.subject.name,
                    'teacher': f"{att.lesson.teacher.first_name} {att.lesson.teacher.last_name}"
                },
                'present': att.present
            })
        return Response({
            'student_id': student.id,
            'student_name': f"{student.first_name} {student.last_name}",
            'total_lessons': total_lessons,
            'attended_lessons': attended_lessons,
            'missed_lessons': missed_lessons,
            'attendance_percentage': round(attendance_percentage, 2),
            'history': records
        })
    




