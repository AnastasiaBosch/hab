from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserRole, Purchase, Book, UserProfile

@receiver(post_save, sender=User)
def create_user_role(sender, instance, created, **kwargs):
    """Создаем роль пользователя при регистрации"""
    if created:
        UserRole.objects.create(user=instance, role='customer')
        UserProfile.objects.create(user=instance)

@receiver(pre_save, sender=Purchase)
def update_book_sales(sender, instance, **kwargs):
    """Обновляем счетчик продаж при доставке заказа"""
    if instance.pk:
        try:
            old_instance = Purchase.objects.get(pk=instance.pk)
            old_status = old_instance.status
        except Purchase.DoesNotExist:
            old_status = None
        
        # Если статус изменился на 'delivered'
        if old_status != 'delivered' and instance.status == 'delivered':
            # Обновляем количество проданных книг
            instance.book.sold_count += instance.quantity
            instance.book.save()
            
            # Обновляем профиль пользователя
            user_profile, created = UserProfile.objects.get_or_create(user=instance.user)
            user_profile.total_purchases += instance.total_price + instance.delivery_cost
            user_profile.save()
            
        # Если отменяем заказ - возвращаем товар
        elif old_status != 'cancelled' and instance.status == 'cancelled':
            instance.book.quantity += instance.quantity
            instance.book.save()
            
        # Если снимаем отмену - списываем товар
        elif old_status == 'cancelled' and instance.status != 'cancelled':
            if instance.book.quantity >= instance.quantity:
                instance.book.quantity -= instance.quantity
                instance.book.save()