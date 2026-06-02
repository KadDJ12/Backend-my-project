from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from .serializer import LessonsSerializer, AttendendanseSerializer, LessonTemplateSerializer
from .models import Lesson, Attendance, LessonTemplate
from Users.permissions import IsAdminRole, IsAdminOrTeacherRole


class LessonsViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonsSerializer
    permission_classes = [IsAdminOrTeacherRole, IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user or user.is_anonymous:
            return Lesson.objects.none()

        if user.is_superuser:
            return Lesson.objects.all()
            
        return Lesson.objects.filter(
            branch__in=user.branches.all()
        ).distinct()
    
    def check_permissions(self, request):
        super().check_permissions(request)
        if request.user.role == 'teacher' and request.method not in ['GET', 'HEAD', 'OPTIONS']:
            self.permission_denied(
                request,
                message='Teacher is not allowed to create or edit lessons.'
            )

    def destroy(self, request, *args, **kwargs):
        lesson = self.get_object()
        lesson.status = 'CANCELLED'
        lesson.save()

        return Response(
            {'message': f'Заняття "{lesson.title if hasattr(lesson, "title") else lesson.id}" успішно скасовано.'}, 
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def teacher_schedule(self, request):
        teacher_id = request.query_params.get('teacher_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not teacher_id:
            return Response({'error': 'teacher_id query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        # Restrict teacher to only see their own schedule
        if user.role == 'teacher' and str(user.id) != str(teacher_id):
            return Response({'error': 'You do not have permission to view other teachers schedule.'}, status=status.HTTP_403_FORBIDDEN)

        queryset = Lesson.objects.filter(teacher_id=teacher_id)

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        # Restrict admin to their assigned branches
        if not user.is_superuser and user.role == 'admin':
            queryset = queryset.filter(branch__in=user.branches.all()).distinct()

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendendanseSerializer
    permission_classes = [IsAdminOrTeacherRole, IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user or user.is_anonymous:
            return Attendance.objects.none()

        if user.is_superuser:
            return Attendance.objects.all()

        return Attendance.objects.filter(
            lesson__branch__in=user.branches.all()
        ).distinct()
    
    def check_permissions(self, request):
        super().check_permissions(request)
        if request.user.role == 'teacher' and request.method not in ['GET', 'POST', 'PUT', 'PATCH', 'HEAD', 'OPTIONS']:
            self.permission_denied(
                request,
                message='Teacher is not allowed to delete attendance records.'
            )

    def destroy(self, request, *args, **kwargs):
        attendance = self.get_object()
        attendance.delete()
        return Response(
            {'message': 'Запис про відвідуваність успішно видалено.'}, 
            status=status.HTTP_200_OK
        )


class LessonTemplateViewSet(viewsets.ModelViewSet):
    queryset = LessonTemplate.objects.all()
    serializer_class = LessonTemplateSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        user = self.request.user
        if not user or user.is_anonymous:
            return LessonTemplate.objects.none()
        if user.is_superuser:
            return LessonTemplate.objects.all()
        return LessonTemplate.objects.filter(branch__in=user.branches.all()).distinct()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        response_data = serializer.data
        
        response_data['lessons_created'] = serializer.context.get('lessons_created_count', 0)
        response_data['conflicts'] = serializer.context.get('conflicts', [])
        
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)