from django.shortcuts import render
from rest_framework import viewsets, views
from rest_framework.decorators import action
from .models import Branch , Subject
from .serializer import BranchSerializer, SubjectSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from Users.permissions import IsAdminRole
from Lessons.models import Attendance



class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated,IsAdminRole]


    def get_queryset(self):
        user = self.request.user
        if not user or user.is_anonymous:
            return Branch.objects.none()
        
        return user.branches.filter(status='active')

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsAdminRole])
    def statistics(self, request, pk=None):
        branch = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        active_students_count = branch.students.filter(status='active').count()
        lessons = branch.lessons.all()
        if start_date:
            lessons = lessons.filter(date__gte=start_date)
        if end_date:
            lessons = lessons.filter(date__lte=end_date)
        total_lessons = lessons.count()

        completed_lessons = lessons.filter(status='COMPLETED').count()
        cancelled_lessons = lessons.filter(status='CANCELLED').count()
        scheduled_lessons = lessons.filter(status='SCHEDULED').count()


        branch_attendances = Attendance.objects.filter(
            lesson__branch=branch,
            lesson__status='COMPLETED'
        )
        if start_date:
            branch_attendances = branch_attendances.filter(lesson__date__gte=start_date)
        if end_date:
            branch_attendances = branch_attendances.filter(lesson__date__lte=end_date)

        total_attendance_records = branch_attendances.count()
        present_attendance_records = branch_attendances.filter(present=True).count()
        attendance_percentage = (present_attendance_records / total_attendance_records * 100) if total_attendance_records > 0 else 0

        return Response({
            'branch_id': branch.id,
            'branch_name': branch.name,
            'active_students_count': active_students_count,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'cancelled_lessons': cancelled_lessons,
            'scheduled_lessons': scheduled_lessons,
            'attendance_percentage': round(attendance_percentage, 2)
        })

    def destroy(self, request, *args, **kwargs):
        from Students.models import Student
        from Lessons.models import Lesson
        branch = self.get_object()
        has_active_students = Student.objects.filter(branch=branch, status='active').exists()
        has_active_lessons = Lesson.objects.filter(branch=branch, status='SCHEDULED').exists()
        if has_active_students or has_active_lessons:
            return Response(
                {'error': 'Неможливо архівувати філію: є активні студенти або плановані уроки.'},
                status=400
            )
        branch.status = 'archived'
        branch.save()
        return Response({'message': f'Філію "{branch.name}" архівовано.'}, status=200)
    
class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        user = self.request.user
        if not user or user.is_anonymous:
            return Subject.objects.none()
        
        return self.queryset.filter(branch__in=user.branches.all(), status='active').distinct()




    # @action(detail=False, methods=['get'], url_path='math')
    # def get_math_subjects(self, request):
    #     queryset = super().get_queryset()
    #     name = self.request.query_params.get('name')
    #     if name is not None:
    #         queryset = queryset.filter(name = name)
    #     return queryset

    # @action(detail=False, methods=['post'], url_path='math')
    # def create_math_subject(self, request):
    #     name = request.data.get('name')
    #     branch_id = request.data.get('branch')
    #     if name is None or branch_id is None:
    #         return Response({'error': 'Name and branch are required.'}, status=400)
    #     data = request.data.copy()
    #     data['name'] = 'Math'
    #     serializer = self.get_serializer(data=data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=201)
    #     return Response(ValueError(serializer.errors), status=400)




    def destroy(self, request, *args, **kwargs):
        subject = self.get_object()
        subject.status = 'archived'
        subject.save()
        return Response({'message': f'Предмет "{subject.name}" архівовано.'}, status=200)
