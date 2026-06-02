from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from Users.permissions import IsAdminRole
from .models import SubscriptionPlan, StudentSubscription
from .serializer import SubscriptionPlanSerializer, StudentSubscriptionSerializer

class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        
        user = self.request.user
        if not user or user.is_anonymous:
            return SubscriptionPlan.objects.none()
        
        if user.is_superuser:
            return SubscriptionPlan.objects.all()
        return SubscriptionPlan.objects.filter(branch__in=user.branches.all()).distinct()

    def destroy(self, request, *args, **kwargs):
        plan = self.get_object()
        plan.status = 'archived'
        plan.save()
        return Response(
            {"message": f"Абонемент '{plan.name}' успішно переведено в статус Archived."},
            status=status.HTTP_200_OK
        )


class StudentSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = StudentSubscription.objects.all()
    serializer_class = StudentSubscriptionSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        user = self.request.user
        if not user or user.is_anonymous:
            return StudentSubscription.objects.none()
            
        if user.is_superuser:
            return StudentSubscription.objects.all()
        return StudentSubscription.objects.filter(student__branch__in=user.branches.all()).distinct()