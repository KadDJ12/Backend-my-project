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
    



class LessonTemplateViewSet(viewsets.ModelViewSet):
    queryset = LessonTemplate.objects.filter(is_active=True)
    serializer_class = LessonTemplateSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacherRole]

    @action(detail=True, methods=['POST'], url_path='generate')
    def generate_lessons(self, request, pk=None):
        """
        Генератор уроків за шаблоном.
        Приймає в body: {"strategy": "block"} або {"strategy": "skip"}
        """
        template = self.get_object()
        strategy = request.data.get('strategy', 'block') # за замовчуванням блокуємо все

        if strategy not in ['block', 'skip']:
            return Response({'error': 'Невідома стратегія. Використовуйте "block" або "skip".'}, status=status.HTTP_400_BAD_REQUEST)

        generated_lessons = []
        skipped_dates = []
        
        current_date = template.start_date
        end_date = template.end_date

        # Робимо всю генерацію в транзакції. Якщо буде блок — база автоматично відкотиться (rollback)
        try:
            with transaction.atomic():
                while current_date <= end_date:
                    # В Python current_date.weekday() повертає 0 для Пн, 6 для Нд
                    if current_date.weekday() in template.days_of_week:
                        
                        # Створюємо екземпляр уроку в пам'яті (без збереження в базу)
                        lesson = Lesson(
                            date=current_date,
                            start_time=template.start_time,
                            end_time=template.end_time,
                            status='SCHEDULED',
                            title=f"Заняття за шаблоном: {template.subject.name}",
                            teacher=template.teacher,
                            subject=template.subject,
                            branch=template.branch,
                            student=template.student,
                            group=template.group
                        )

                        try:
                            # Запускаємо твою круту бізнес-валідацію конфліктів розкладу
                            lesson.full_clean()
                            lesson.save() # Якщо все ок — зберігаємо
                            generated_lessons.append(lesson)
                        
                        except DjangoValidationError as e:
                            # Опа, зловили конфлікт розкладу!
                            error_msg = str(e)
                            if strategy == 'block':
                                # Стратегія BLOCK: Перериваємо транзакцію, нічого не створюється
                                return Response({
                                    'error': f'Конфлікт розкладу на дату {current_date.strftime("%Y-%m-%d")}. Генерацію повністю заблоковано.',
                                    'details': error_msg
                                }, status=status.HTTP_409_CONFLICT)
                            else:
                                # Стратегія SKIP: Запам'ятовуємо проблемну дату і йдемо далі
                                skipped_dates.append({
                                    'date': current_date.strftime('%Y-%m-%d'),
                                    'reason': error_msg
                                })

                    current_date += timedelta(days=1) # Переходимо до наступного дня

        except Exception as p_err:
            return Response({'error': f'Внутрішня помилка генерації: {str(p_err)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Повертаємо детальний звіт для фронтенду
        return Response({
            'message': f'Генерацію успішно завершено за стратегією "{strategy}".',
            'created_count': len(generated_lessons),
            'skipped_count': len(skipped_dates),
            'skipped_details': skipped_dates,
            'lessons': LessonsSerializer(generated_lessons, many=True).data
        }, status=status.HTTP_201_CREATED)