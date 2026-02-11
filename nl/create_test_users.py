import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nl.settings')
django.setup()

from django.contrib.auth.models import User
from catalog.models import UserRole

def create_test_users():
    # Удаляем старые роли и пользователей
    users_to_delete = User.objects.filter(username__in=['staff', 'courier', 'customer'])
    UserRole.objects.filter(user__in=users_to_delete).delete()
    users_to_delete.delete()
    
    # 1. Создаем сотрудника магазина
    staff_user = User.objects.create_user(
        username='staff',
        email='staff@example.com',
        password='staff123',
        first_name='Иван',
        last_name='Сотрудников',
        is_staff=True,
        is_active=True
    )
    # Обновляем существующую роль, созданную сигналом
    staff_user.role.role = 'staff'
    staff_user.role.save()
    print(f"✅ Создан сотрудник: staff / staff123")
    courier_user = User.objects.create_user(
        username='courier',
        email='courier@example.com',
        password='courier123',
        first_name='Петр',
        last_name='Курьеров',
        is_staff=True, 
        is_active=True
    )
    courier_user.role.role = 'courier'
    courier_user.role.save()
    print(f"✅ Создан курьер: courier / courier123")
    customer_user = User.objects.create_user(
        username='customer',
        email='customer@example.com',
        password='customer123',
        first_name='Алексей',
        last_name='Покупателев',
        is_staff=False,  
        is_active=True
    )
    print(f"✅ Создан покупатель: customer / customer123")
    
    print("\n" + "="*50)
    print("Тестовые пользователи созданы!")
    print("="*50)
    print("\nДоступ к CRM имеют:")
    print("  • Сотрудник")
    print("  • Курьер")
    print("\nДля входа используйте:")
    print("  • Логин: staff, Пароль: staff123")
    print("  • Логин: courier, Пароль: courier123")
    print("\nПокупатель может только покупать на сайте:")

if __name__ == '__main__':
    create_test_users()