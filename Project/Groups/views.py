from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from django.utils import timezone
from .models import Group, GroupMembership
from Students.models import Student
from .serializer import GroupSerializer
from Users.permissions import IsAdminOrTeacherRole, IsAdminRole
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminOrTeacherRole, IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
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

        if request.user.role == 'teacher' and request.method not in ['GET', 'HEAD', 'OPTIONS']:
            self.permission_denied(request, message='Teacher is not allowed to create or edit groups')
    
    def destroy(self, request, *args, **kwargs):
        group = self.get_object()
        group.status = 'archived'
        group.save()

        return Response(
            {'message': f'Групу "{group.name}" успішно переведено в статус Archived.'}, 
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminRole])
    def add_student(self, request, pk=None):
        group = self.get_object()
        student_id = request.data.get('student_id')
        
        if not student_id:
            return Response({'error': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
            
        # Edge Case: Cannot add a student from a different branch to a group
        if student.branch != group.branch:
            return Response({'error': 'Cannot add a student from a different branch to this group'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Check if student is active
        if student.status != 'active':
            return Response({'error': 'Cannot add an inactive student to a group'}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create group membership
        membership, created = GroupMembership.objects.get_or_create(
            group=group,
            student=student
        )
        
        if not created and membership.leave_date is None:
            return Response({'message': 'Student is already an active member of this group'}, status=status.HTTP_200_OK)
            
        # If student was previously removed, we re-activate them
        membership.join_date = timezone.now().date()
        membership.leave_date = None
        membership.save()
        
        return Response({'message': f'Student {student.first_name} {student.last_name} successfully added to group.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminRole])
    def remove_student(self, request, pk=None):
        group = self.get_object()
        student_id = request.data.get('student_id')
        
        if not student_id:
            return Response({'error': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
            
        try:
            membership = GroupMembership.objects.get(group=group, student=student, leave_date__isnull=True)
        except GroupMembership.DoesNotExist:
            return Response({'error': 'Student is not an active member of this group'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Soft remove: record leave date
        membership.leave_date = timezone.now().date()
        membership.save()
        
        return Response({'message': f'Student {student.first_name} {student.last_name} successfully removed from group.'}, status=status.HTTP_200_OK)
        

            
    



    