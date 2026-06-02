from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from .serializer import LessonsSerializer, AttendendanseSerializer
from .models import Lesson, Attendance
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
            {'message': f'Заняття "{lesson.name if hasattr(lesson, "name") else lesson.id}" успішно скасовано.'}, 
            status=status.HTTP_200_OK
        )  
    



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