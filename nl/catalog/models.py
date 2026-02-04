from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal

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
    
    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

    @property
    def is_available(self):
        """Проверка"""
        return self.quantity > 0
    
    def reduce_quantity(self, amount=1):
        """Уменьшает"""
        if self.quantity >= amount:
            self.quantity -= amount
            self.save()
            return True
        return False
    
    def increase_quantity(self, amount=1):
        """Увеличивает"""
        self.quantity += amount
        self.save()

    def get_absolute_url(self):
        return reverse('book-detail', args=[str(self.id)])

    def display_genre(self):
        """
        Creates a string for the Genre. This is required to display genre in Admin.
        """
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
    """Профиль пользователя с информацией о покупках и скидках"""
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
        """Рассчитывает процент скидки"""
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
    """Модель для учета покупок пользователей"""
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

    class Meta:
        ordering = ['-purchase_date']
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
    
    def __str__(self):
        return f'{self.user.username} - {self.book.title}'
    
    def get_status_display_with_color(self):
        """Статус с иконкой"""
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
        if not self.delivery_cost and self.delivery_method:
            self.delivery_cost = self.calculate_delivery_cost(self.quantity)
    
        super().save(*args, **kwargs)
        
        user_profile, created = UserProfile.objects.get_or_create(user=self.user)
        
        total = Decimal('0')
        for purchase in self.user.purchases.exclude(status='cancelled'):
            total += purchase.total_price + purchase.delivery_cost
        
        user_profile.total_purchases = total
        user_profile.save()