from django.shortcuts import render
from .serializers import StudentSerializer
from rest_framework import viewsets,status
from Users.permissions import IsAdminOrTeacherRole
from rest_framework.permissions import IsAuthenticated
from .models import Student
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response




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
        student.status = 'dropped'
        student.save()

        return Response(
            {
                'message': f'Студента {student.first_name} {student.last_name} переведено в статус Dropped (архівовано). '
                           f'Якщо він завершив навчання, змініть статус на Graduated через PATCH.'
            }, 
            status=status.HTTP_200_OK
        )  




