from django.contrib import admin
from .models import Author, Genre, Book, News, UserProfile, Purchase


admin.site.register(Genre)

class AuthorAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name')
admin.site.register(Author, AuthorAdmin)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'display_genre','price', 'quantity')
    fields = ['title', 'avatar', 'author', 'summary', 'genre', 'price', 'quantity']

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_date', 'is_published')
    list_filter = ('published_date', 'is_published')
    search_fields = ('title', 'content')
    date_hierarchy = 'published_date'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_purchases', 'discount_percent')
    list_filter = ('user__is_active',)
    search_fields = ('user__username', 'user__email')
    
    def discount_percent(self, obj):
        return f"{obj.discount_percent}%"
    discount_percent.short_description = 'Текущая скидка'

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'quantity', 'price', 'total_price', 'purchase_date', 'get_payment_method')
    list_filter = ('purchase_date', 'user', 'payment_method')  
    search_fields = ('user__username', 'book__title')
    date_hierarchy = 'purchase_date'
    
    def get_payment_method(self, obj):
        return dict(obj.PAYMENT_CHOICES).get(obj.payment_method, obj.payment_method)
    get_payment_method.short_description = 'Способ оплаты'