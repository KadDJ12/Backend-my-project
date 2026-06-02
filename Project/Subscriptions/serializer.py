from rest_framework import serializers
from .models import SubscriptionPlan, PlanPriceTier, StudentSubscription


class PlanPriceTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanPriceTier
        fields = ['id', 'lessons_per_month', 'price_per_lesson']


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    # Дозволяє створювати сітку цін прямо при створенні плану
    price_tiers = PlanPriceTierSerializer(many=True, required=False)
    
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'type', 'status', 'branch', 'subjects', 'price_tiers', 'created_at']

    def create(self, validated_data):
        price_tiers_data = validated_data.pop('price_tiers', [])
        subjects_data = validated_data.pop('subjects', [])
        
        # Створюємо план
        subscription_plan = SubscriptionPlan.objects.create(**validated_data)
        subscription_plan.subjects.set(subjects_data)
        
        # Додаємо сітку цін
        for tier_data in price_tiers_data:
            PlanPriceTier.objects.create(subscription_plan=subscription_plan, **tier_data)
            
        return subscription_plan

    def update(self, instance, validated_data):
        price_tiers_data = validated_data.pop('price_tiers', None)
        subjects_data = validated_data.pop('subjects', None)
        
        instance = super().update(instance, validated_data)
        
        if subjects_data is not None:
            instance.subjects.set(subjects_data)
            
        if price_tiers_data is not None:
            # Оновлюємо цінову сітку: видаляємо старі записи та створюємо нові
            instance.price_tiers.all().delete()
            for tier_data in price_tiers_data:
                PlanPriceTier.objects.create(subscription_plan=instance, **tier_data)
                
        return instance


class StudentSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentSubscription
        fields = ['id', 'student', 'subject', 'subscription_plan', 'start_date']

    def validate(self, data):
        student = data.get('student')
        subject = data.get('subject')
        subscription_plan = data.get('subscription_plan')

        if student.branch != subject.branch:
            raise serializers.ValidationError("Студент та предмет мають належати до однієї філії.")
            
        if subscription_plan.branch != student.branch:
            raise serializers.ValidationError("Обраний абонемент належить до іншої філії.")

        if subject not in subscription_plan.subjects.all():
            raise serializers.ValidationError(
                f"Абонемент '{subscription_plan.name}' не поширюється на предмет '{subject.name}'."
            )

        if not self.instance:  # Перевірка тільки при створенні нової підписки
            if subscription_plan.status == 'archived':
                raise serializers.ValidationError("Неможливо призначити архівований абонемент.")

        existing = StudentSubscription.objects.filter(student=student, subject=subject)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError("У цього студента вже є активний абонемент на цей предмет.")

        return data