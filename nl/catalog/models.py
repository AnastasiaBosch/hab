from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone

class Genre(models.Model):
    name = models.CharField(max_length=200, help_text="Укажите жанр книги (например, научная фантастика, французская поэзия и т.д.)")

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True)
    summary = models.TextField(max_length=1000, help_text="Введите краткое описание книги")
    genre = models.ManyToManyField(Genre, help_text="Select a genre for this book")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена", default=0)
    quantity = models.PositiveIntegerField(default=0, verbose_name="Количество на складе")
    sold_count = models.PositiveIntegerField(default=0, verbose_name="Количество проданных копий")
    
    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

    @property
    def is_available(self):
        return self.quantity > 0
    
    def reduce_quantity(self, amount=1):
        if self.quantity >= amount:
            self.quantity -= amount
            self.save()
            return True
        return False
    
    def increase_quantity(self, amount=1):
        self.quantity += amount
        self.save()

    def get_absolute_url(self):
        return reverse('book-detail', args=[str(self.id)])

    def display_genre(self):
        return ', '.join([ genre.name for genre in self.genre.all()[:3] ])
    display_genre.short_description = 'Genre'
    
class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def get_absolute_url(self):
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        return '%s, %s' % (self.last_name, self.first_name)

class News(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок новости")
    content = models.TextField(verbose_name="Содержание новости")
    published_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    
    class Meta:
        ordering = ['-published_date']
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
    
    def __str__(self):
        return self.title
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    total_purchases = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Общая сумма покупок"
    )
    
    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
    
    def __str__(self):
        return f'Профиль {self.user.username}'
    
    @property
    def discount_percent(self):
        if self.total_purchases >= 50000:
            return 10
        elif self.total_purchases >= 30000:
            return 8
        elif self.total_purchases >= 15000:
            return 6
        elif self.total_purchases >= 7000:
            return 4
        elif self.total_purchases >= 3000:
            return 2
        else:
            return 0

class Purchase(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Наличные при получении'),
        ('card', 'Картой при получении'),
    ]

    DELIVERY_CHOICES = [
        ('pickup', 'Самовывоз (бесплатно)'),
        ('krasnoyarsk', 'Доставка по Красноярску (400 ₽)'),
        ('russia', 'Доставка по России и миру'),
    ]

    STATUS_CHOICES = [
        ('created', '🟡 Создан'),
        ('assembled', '🟠 Собран'),
        ('shipped', '🔵 Доставляется'),
        ('delivered', '🟢 Доставлен'),
        ('cancelled', '🔴 Отменен'),
    ]

    # Основные поля
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за единицу")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая стоимость")
    purchase_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата покупки")
    
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_CHOICES,
        default='cash',
        verbose_name="Способ оплаты"
    )

    delivery_method = models.CharField(
        max_length=15,
        choices=DELIVERY_CHOICES,
        default='pickup',
        verbose_name="Способ доставки"
    )

    delivery_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Стоимость доставки"
    )
    
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='created',
        verbose_name="Статус заказа"
    )
    
    # Поля для подтверждений
    staff_confirmed_shipping = models.BooleanField(
        default=False, 
        verbose_name="Подтверждена сборка (сотрудником)"
    )
    courier_confirmed_shipping = models.BooleanField(
        default=False, 
        verbose_name="Подтвержден прием (курьером)"
    )
    staff_confirmed_delivery = models.BooleanField(
        default=False, 
        verbose_name="Подтверждена доставка (сотрудником)"
    )
    courier_confirmed_delivery = models.BooleanField(
        default=False, 
        verbose_name="Подтверждена доставка (курьером)"
    )
    
    # Кто подтвердил
    confirmed_by_staff = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='confirmed_shipping_staff',
        verbose_name="Подтвердил сборку (сотрудник)"
    )
    confirmed_by_courier = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='confirmed_delivery_courier',
        verbose_name="Подтвердил доставку (курьер)"
    )
    confirmation_date = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Дата подтверждения"
    )
    
    # Дополнительные поля
    delivery_time = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Время доставки"
    )
    recipient_name = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name="Имя получившего"
    )
    notes = models.TextField(
        null=True, 
        blank=True, 
        verbose_name="Комментарии"
    )
    
    # Дополнительные поля для форм
    pickup_code = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Код выдачи"
    )
    delivery_notes = models.TextField(
        null=True,
        blank=True,
        verbose_name="Комментарий к доставке"
    )

    class Meta:
        ordering = ['-purchase_date']
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
    
    def __str__(self):
        return f'Заказ #{self.id}: {self.user.username} - {self.book.title}'
    
    def get_status_display_with_color(self):
        for code, name in self.STATUS_CHOICES:
            if code == self.status:
                return name
        return self.status
    
    def get_delivery_display(self):
        for code, name in self.DELIVERY_CHOICES:
            if code == self.delivery_method:
                return name
        return self.delivery_method
    
    def calculate_delivery_cost(self, total_books=1):
        if self.delivery_method == 'pickup':
            return 0
        elif self.delivery_method == 'krasnoyarsk':
            return 400
        elif self.delivery_method == 'russia':
            return 250 + (max(0, total_books - 1) * 50)
        return 0
    
    def save(self, *args, **kwargs):
        # Автоматически рассчитываем стоимость доставки при сохранении
        if not self.delivery_cost and self.delivery_method:
            self.delivery_cost = self.calculate_delivery_cost(self.quantity)
        
        super().save(*args, **kwargs)

class UserRole(models.Model):
    ROLE_CHOICES = [
        ('courier', 'Курьер'),
        ('staff', 'Сотрудник магазина'),
        ('customer', 'Покупатель'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='role')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    
    class Meta:
        verbose_name = 'Роль пользователя'
        verbose_name_plural = 'Роли пользователей'
    
    def __str__(self):
        return f'{self.user.username} - {self.get_role_display()}'
    
    @property
    def is_courier(self):
        return self.role == 'courier'
    
    @property
    def is_staff(self):
        return self.role == 'staff'
    
    @property
    def is_customer(self):
        return self.role == 'customer'