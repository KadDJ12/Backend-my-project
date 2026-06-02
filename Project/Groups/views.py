from django.shortcuts import render
from rest_framework import viewsets,status
from .models import Group
from .serializer import GroupSerializer
from Users.permissions import IsAdminOrTeacherRole
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response






class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminOrTeacherRole,IsAuthenticated]
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields = ['id', 'branch', 'status']
    search_fields = ['name']

    def get_queryset(self):
        user = self.request.user
        if not user or user.is_anonymous:
            return Group.objects.none()

        if user.is_superuser:
            return Group.objects.all()
            
        return Group.objects.filter(
            branch__in=user.branches.all(),
            status='active').distinct()

    def check_permissions(self, request):
        super().check_permissions(request)

        if request.user.role == 'teacher' and request.method not in ['GET','HEAD','OPTIONS']:
            self.permission_denied(request,message='Teacher is not allowed to create or edit students')
    
    def destroy(self, request, *args, **kwargs):
        group = self.get_object()
        group.status = 'archived'
        group.save()

        return Response(
            {'message': f'Групу "{group.name}" успішно переведено в статус Archived.'}, 
            status=status.HTTP_200_OK
        )
        

            
    



    