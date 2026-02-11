from django.contrib import admin
from .models import Author, Genre, Book, News, UserProfile, Purchase
from .models import UserRole

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
    list_display = ('user', 'book', 'quantity', 'price', 'total_price', 'delivery_method', 'status', 'purchase_date', 'staff_confirmed_shipping', 'courier_confirmed_shipping',
                    'staff_confirmed_delivery', 'courier_confirmed_delivery',)
    list_filter = ('purchase_date', 'user', 'payment_method', 'delivery_method', 'status', 'staff_confirmed_shipping', 'courier_confirmed_shipping',
                    'staff_confirmed_delivery', 'courier_confirmed_delivery',)
    search_fields = ('user__username', 'book__title')
    date_hierarchy = 'purchase_date'
    list_editable = ('status',)
    
    def get_status_display(self, obj):
        return dict(obj.STATUS_CHOICES).get(obj.status, obj.status)
    get_status_display.short_description = 'Статус'
    
    def get_payment_method(self, obj):
        return dict(obj.PAYMENT_CHOICES).get(obj.payment_method, obj.payment_method)
    get_payment_method.short_description = 'Способ оплаты'
    
    def get_delivery_method(self, obj):
        return dict(obj.DELIVERY_CHOICES).get(obj.delivery_method, obj.delivery_method)
    get_delivery_method.short_description = 'Способ доставки'

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Purchase.objects.get(pk=obj.pk)
            
            if obj.status == 'cancelled' and old_obj.status != 'cancelled':
                obj.book.quantity += obj.quantity
                obj.book.save()
                
            elif old_obj.status == 'cancelled' and obj.status != 'cancelled':
                if obj.book.quantity >= obj.quantity:
                    obj.book.quantity -= obj.quantity
                    obj.book.save()
        
        super().save_model(request, obj, form, change)

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'user_email')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def save_model(self, request, obj, form, change):
        if obj.role == 'staff' and not obj.user.is_staff:
            obj.user.is_staff = True
            obj.user.save()
        super().save_model(request, obj, form, change)