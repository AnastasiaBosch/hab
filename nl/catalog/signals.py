from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserRole, Purchase, Book

@receiver(post_save, sender=User)
def create_user_role(sender, instance, created, **kwargs):
    """Создаем роль пользователя при регистрации"""
    if created:
        UserRole.objects.create(user=instance, role='customer')

@receiver(post_save, sender=Purchase)
def update_book_sales(sender, instance, created, **kwargs):
    """Обновляем счетчик продаж при доставке заказа"""
    if instance.status == 'delivered':
        if not hasattr(instance, '_sales_updated'):
            instance.book.sold_count += instance.quantity
            instance.book.save()
            instance._sales_updated = True

@receiver(post_save, sender=Purchase)
def update_book_sales(sender, instance, created, **kwargs):
    """Обновляем счетчик продаж при доставке заказа"""
    if instance.status == 'delivered':
        # Получаем старую версию заказа до сохранения
        if instance.pk:
            try:
                old_instance = Purchase.objects.get(pk=instance.pk)
                old_status = old_instance.status
            except Purchase.DoesNotExist:
                old_status = None
            
            # Если статус изменился на 'delivered'
            if old_status != 'delivered':
                instance.book.sold_count += instance.quantity
                instance.book.save()