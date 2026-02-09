from django.shortcuts import redirect
from django.contrib import messages

class SimpleRoleMixin:
    """Простой миксин для проверки ролей"""
    allowed_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Суперпользователь имеет доступ ко всему
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        
        # Проверяем, что пользователь активен
        if not request.user.is_active:
            messages.error(request, 'Ваш аккаунт деактивирован')
            return redirect('logout')
        
        # Проверяем роль пользователя
        try:
            user_role = request.user.role.role
        except:
            from .models import UserRole
            UserRole.objects.create(user=request.user, role='customer')
            user_role = 'customer'
        
        # Проверяем доступ по роли
        if self.allowed_roles and user_role not in self.allowed_roles:
            messages.error(request, 'У вас нет прав для доступа к этой странице')
            return redirect('index')  # Перенаправляем на главную магазина
        
        return super().dispatch(request, *args, **kwargs)