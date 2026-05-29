from django.shortcuts import render
from rest_framework import viewsets, views
from rest_framework.decorators import action
from .models import Branch , Subject
from .serializer import BranchSerializer, SubjectSerializer
from rest_framework.response import Response



class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

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

        

