# create_test_users.py (в корне проекта)

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nl.settings')
django.setup()

from django.contrib.auth.models import User
from catalog.models import UserRole

def create_test_users():
    # Удаляем старые роли и пользователей
    users_to_delete = User.objects.filter(username__in=['staff', 'courier', 'customer'])
    
    # Сначала удаляем связанные роли
    UserRole.objects.filter(user__in=users_to_delete).delete()
    
    # Затем удаляем самих пользователей
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
    
    # 2. Создаем курьера
    courier_user = User.objects.create_user(
        username='courier',
        email='courier@example.com',
        password='courier123',
        first_name='Петр',
        last_name='Курьеров',
        is_staff=True,  # Курьеру нужен доступ к CRM
        is_active=True
    )
    # Обновляем существующую роль, созданную сигналом
    courier_user.role.role = 'courier'
    courier_user.role.save()
    print(f"✅ Создан курьер: courier / courier123")
    
    # 3. Создаем покупателя (у него уже будет роль 'customer' от сигнала)
    customer_user = User.objects.create_user(
        username='customer',
        email='customer@example.com',
        password='customer123',
        first_name='Алексей',
        last_name='Покупателев',
        is_staff=False,  # Покупателю НЕ нужен доступ к CRM
        is_active=True
    )
    # Роль 'customer' уже создана сигналом - ничего не делаем
    print(f"✅ Создан покупатель: customer / customer123")
    
    print("\n" + "="*50)
    print("Тестовые пользователи созданы!")
    print("="*50)
    print("\nДоступ к CRM имеют:")
    print("  • Сотрудник: http://127.0.0.1:8000/crm/staff/")
    print("  • Курьер: http://127.0.0.1:8000/crm/courier/")
    print("\nДля входа используйте:")
    print("  • Логин: staff, Пароль: staff123")
    print("  • Логин: courier, Пароль: courier123")
    print("\nПокупатель может только покупать на сайте:")

if __name__ == '__main__':
    create_test_users()