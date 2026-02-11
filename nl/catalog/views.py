from django.shortcuts import render, redirect, get_object_or_404
from .models import Book, Author, Genre, News, UserProfile, Purchase, UserRole
from django.views import generic
from django.urls import reverse
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User 
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from decimal import Decimal
from .mixins import SimpleRoleMixin
from django.views.generic import ListView, UpdateView, CreateView, TemplateView
import datetime
from .forms import UserRegisterForm
from django.utils import timezone

def index(request):
    num_books = Book.objects.all().count()
    num_authors = Author.objects.count()
    num_genres = Genre.objects.count()
    num_news = News.objects.filter(is_published=True).count()

    news_list = News.objects.filter(is_published=True).order_by('-published_date')[:5]
     
    return render(
        request,
        'index.html',
        context={
            'num_books': num_books,
            'num_authors': num_authors,
            'num_genres': num_genres,
            'num_news': num_news,
            'news_list': news_list,
        }
    )

class BookListView(generic.ListView):
    model = Book
    paginate_by = 10
    template_name = 'catalog/book_list.html'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        search_query = self.request.GET.get('search', '')
        genre_id = self.request.GET.get('genre')
        is_available = self.request.GET.get('is_available')
        
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(author__first_name__icontains=search_query) |
                Q(author__last_name__icontains=search_query)
            )
        
        if genre_id:
            queryset = queryset.filter(genre__id=genre_id)
            
        if is_available:
            queryset = queryset.filter(quantity__gt=0)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['genres'] = Genre.objects.all()
        context['search_query'] = self.request.GET.get('search', '')
        return context
    
class BookDetailView(generic.DetailView):
    model = Book

class NewsListView(generic.ListView):
    model = News
    template_name = 'catalog/news_list.html'
    paginate_by = 10
    
    def get_queryset(self):
        return News.objects.filter(is_published=True).order_by('-published_date')

class NewsDetailView(generic.DetailView):
    model = News
    template_name = 'catalog/news_detail.html'
    
    def get_queryset(self):
        return News.objects.filter(is_published=True)

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10
    template_name = 'catalog/author_list.html'

class AuthorDetailView(generic.DetailView):
    model = Author
    template_name = 'catalog/author_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['books_by_author'] = Book.objects.filter(author=self.object)
        return context

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Создан аккаунт {username}!')
            return redirect('login')
    else:
        form = UserRegisterForm()
    
    return render(request, 'catalog/registration/register.html', {'form': form})

@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'catalog/registration/profile.html', {
        'user': request.user,
        'profile': profile,
    })

@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('login')

@login_required
def purchase_history(request):
    purchases = Purchase.objects.filter(user=request.user).order_by('-purchase_date')
    total_spent = sum(p.total_price + p.delivery_cost for p in purchases)
    
    return render(request, 'catalog/purchase_history.html', {
        'purchases': purchases,
        'total_spent': total_spent,
    })

def cart_view(request):
    cart = request.session.get('cart', {})
    
    cart_items = []
    total_price = 0
    
    for book_id, quantity in cart.items():
        try:
            book = Book.objects.get(id=book_id)
            item_total = book.price * quantity
            cart_items.append({
                'book': book,
                'quantity': quantity,
                'total': item_total
            })
            total_price += item_total
        except Book.DoesNotExist:
            pass
    
    return render(request, 'catalog/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })

def add_to_cart(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    cart = request.session.get('cart', {})
    cart[str(book_id)] = cart.get(str(book_id), 0) + 1
    request.session['cart'] = cart
    messages.success(request, f'"{book.title}" добавлена в корзину')
    return redirect('book-detail', pk=book_id)

def remove_from_cart(request, book_id):
    cart = request.session.get('cart', {})
    
    if str(book_id) in cart:
        del cart[str(book_id)]
        request.session['cart'] = cart
        messages.success(request, 'Книга удалена из корзины')
    
    return redirect('cart')

def update_cart_quantity(request, book_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            cart = request.session.get('cart', {})
            cart[str(book_id)] = quantity
            request.session['cart'] = cart
        else:
            return remove_from_cart(request, book_id)
    
    return redirect('cart')

def clear_cart(request):
    request.session['cart'] = {}
    messages.success(request, 'Корзина очищена')
    return redirect('cart')

@login_required
def checkout(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Войдите, чтобы оформить заказ')
        return redirect('login')
    
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.warning(request, 'Ваша корзина пуста')
        return redirect('cart')
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'cash')
        delivery_method = request.POST.get('delivery_method', 'pickup')
        
        unavailable_items = []
        for book_id_str, quantity in cart.items():
            book_id = int(book_id_str)
            book = get_object_or_404(Book, id=book_id)
            
            if book.quantity < quantity:
                unavailable_items.append(book.title)
        
        if unavailable_items:
            messages.error(request, f'Нет в наличии: {", ".join(unavailable_items)}')
            return redirect('cart')
        
        total_books = sum(cart.values())
        total_price = Decimal('0')
        
        for book_id_str, quantity in cart.items():
            book_id = int(book_id_str)
            book = get_object_or_404(Book, id=book_id)
            item_total = book.price * quantity
            
            profile = request.user.profile
            discount = profile.discount_percent
            item_discount = item_total * Decimal(discount) / Decimal('100')
            item_final_price = item_total - item_discount
            
            # Рассчитываем стоимость доставки для каждого товара
            if delivery_method == 'pickup':
                delivery_cost = Decimal('0')
            elif delivery_method == 'krasnoyarsk':
                delivery_cost = Decimal('400')
            elif delivery_method == 'russia':
                base_cost = Decimal('250') + (max(0, total_books - 1) * Decimal('50'))
                delivery_cost = base_cost
            else:
                delivery_cost = Decimal('0')
            
            Purchase.objects.create(
                user=request.user,
                book=book,
                quantity=quantity,
                price=book.price,
                total_price=item_final_price,
                payment_method=payment_method,
                delivery_method=delivery_method,
                delivery_cost=delivery_cost,
                status='created'
            )
            book.quantity -= quantity
            book.save()
            total_price += item_final_price + delivery_cost
        
        request.session['cart'] = {}
        
        payment_display = 'Наличные при получении' if payment_method == 'cash' else 'Картой при получении'
        
        delivery_display = {
            'pickup': 'Самовывоз (бесплатно)',
            'krasnoyarsk': 'Доставка по Красноярску (400 ₽)',
            'russia': f'Доставка по России ({delivery_cost:.0f} ₽)',
        }.get(delivery_method, 'Не указано')
        
        messages.success(
            request, 
            f'✅ Заказ оформлен! Статус: 🟡 Создан<br>'
            f'Сумма: {total_price:.2f} руб.<br>'
            f'Способ оплаты: {payment_display}<br>'
            f'Способ доставки: {delivery_display}'
        )
        
        return redirect('profile')
    
    # GET запрос
    total_price = Decimal('0')
    cart_items = []
    total_books = 0
    
    for book_id_str, quantity in cart.items():
        book_id = int(book_id_str)
        book = get_object_or_404(Book, id=book_id)
        item_total = book.price * quantity
        cart_items.append({
            'book': book,
            'quantity': quantity,
            'total': item_total
        })
        total_price += item_total
        total_books += quantity
    
    profile = request.user.profile
    discount = profile.discount_percent
    discount_amount = total_price * Decimal(discount) / Decimal('100')
    price_without_delivery = total_price - discount_amount
    
    return render(request, 'catalog/checkout.html', {
        'cart_items': cart_items,
        'total_price': float(total_price),
        'total_books': total_books,
        'discount': discount,
        'discount_amount': float(discount_amount),
        'price_without_delivery': float(price_without_delivery),
    })

class StaffDashboardView(SimpleRoleMixin, TemplateView):
    template_name = 'catalog/staff/dashboard.html'
    allowed_roles = ['staff']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = datetime.date.today()
        today_orders = Purchase.objects.filter(
            purchase_date__date=today
        )
        
        low_stock = Book.objects.filter(quantity__lt=3)
        
        context.update({
            'today_orders_count': today_orders.count(),
            'today_revenue': sum(o.total_price + o.delivery_cost for o in today_orders),
            'low_stock': low_stock,
            'total_books': Book.objects.count(),
            'active_orders': Purchase.objects.exclude(
                status__in=['delivered', 'cancelled']
            ).count(),
        })
        
        return context

class ManageOrdersView(SimpleRoleMixin, ListView):
    model = Purchase
    template_name = 'catalog/staff/orders.html'
    context_object_name = 'orders'
    allowed_roles = ['staff']
    paginate_by = 20
    
    def get_queryset(self):
        status = self.request.GET.get('status', '')
        queryset = Purchase.objects.all().order_by('-purchase_date')
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['status_choices'] = Purchase.STATUS_CHOICES 
        return context

@login_required
def change_status_form(request, purchase_id):
    """Форма для изменения статуса"""
    purchase = get_object_or_404(Purchase, id=purchase_id)
    
    if not (hasattr(request.user, 'role') and request.user.role.role == 'staff'):
        messages.error(request, 'Нет прав')
        return redirect('index')
    
    return render(request, 'catalog/staff/change_status.html', {
        'purchase': purchase
    })

@login_required
def change_order_status(request, purchase_id):
    """Простая функция изменения статуса заказа (для сотрудника)"""
    purchase = get_object_or_404(Purchase, id=purchase_id)
    
    if not (hasattr(request.user, 'role') and request.user.role.role == 'staff'):
        messages.error(request, 'Нет прав для изменения статуса')
        return redirect('index')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        # Простая логика смены статусов
        allowed_statuses = dict(Purchase.STATUS_CHOICES).keys()
        
        if new_status in allowed_statuses:
            old_status = purchase.status
            
            # Если отменяем заказ - возвращаем товар на склад
            if old_status != 'cancelled' and new_status == 'cancelled':
                purchase.book.quantity += purchase.quantity
                purchase.book.save()
            # Если снимаем отмену - снова списываем товар
            elif old_status == 'cancelled' and new_status != 'cancelled':
                if purchase.book.quantity < purchase.quantity:
                    messages.error(request, f'Недостаточно товара на складе. Доступно: {purchase.book.quantity}')
                    return redirect('staff_orders')
                purchase.book.quantity -= purchase.quantity
                purchase.book.save()
            
            purchase.status = new_status
            purchase.notes = notes
            
            # Если доставлен - обновляем статистику
            if new_status == 'delivered':
                purchase.delivery_time = timezone.now()
                purchase.book.sold_count += purchase.quantity
                purchase.book.save()
                
                user_profile, created = UserProfile.objects.get_or_create(user=purchase.user)
                user_profile.total_purchases += purchase.total_price + purchase.delivery_cost
                user_profile.save()
            
            purchase.save()
            messages.success(request, f'Статус заказа #{purchase.id} изменен на {purchase.get_status_display()}')
        else:
            messages.error(request, 'Некорректный статус')
    
    return redirect('staff_orders')

@login_required
def confirm_shipping_staff(request, purchase_id):
    """Сотрудник подтверждает готовность к отправке"""
    purchase = get_object_or_404(Purchase, id=purchase_id)
    
    if not (hasattr(request.user, 'role') and request.user.role.role == 'staff'):
        messages.error(request, 'Нет прав')
        return redirect('index')
    
    if request.method == 'POST':
        purchase.staff_confirmed_shipping = True
        purchase.confirmed_by_staff = request.user
        purchase.confirmation_date = timezone.now()
        purchase.status = 'assembled'  # Меняем статус на "Собран"
        purchase.save()
        
        messages.success(request, f'Подтверждена готовность к отправке заказа #{purchase.id}')
        
        return redirect('staff_orders')
    
    return render(request, 'catalog/staff/confirm_shipping.html', {'purchase': purchase})

@login_required
def confirm_delivery_staff(request, purchase_id):
    """Сотрудник подтверждает завершение доставки"""
    purchase = get_object_or_404(Purchase, id=purchase_id)
    
    if not (hasattr(request.user, 'role') and request.user.role.role == 'staff'):
        messages.error(request, 'Нет прав')
        return redirect('index')
    
    if request.method == 'POST':
        purchase.staff_confirmed_delivery = True
        purchase.confirmed_by_staff = request.user
        purchase.confirmation_date = timezone.now()
        
        # Если и курьер подтвердил, завершаем доставку
        if purchase.courier_confirmed_delivery:
            purchase.status = 'delivered'
            purchase.delivery_time = timezone.now()
            purchase.save()
            messages.success(request, f'Заказ #{purchase.id} завершен')
        else:
            purchase.save()
            messages.success(request, f'Подтверждено завершение доставки заказа #{purchase.id}')
        
        return redirect('staff_orders')
    
    return render(request, 'catalog/staff/confirm_delivery.html', {'purchase': purchase})

@login_required
def confirm_shipping_courier(request, purchase_id):
    """Курьер подтверждает получение заказа"""
    purchase = get_object_or_404(Purchase, id=purchase_id)
    
    if not (hasattr(request.user, 'role') and request.user.role.role == 'courier'):
        messages.error(request, 'Только курьер может подтверждать получение')
        return redirect('index')
    
    if purchase.delivery_method == 'pickup':
        messages.error(request, 'Это заказ на самовывоз')
        return redirect('courier_orders')
    
    if request.method == 'POST':
        purchase.courier_confirmed_shipping = True
        purchase.confirmed_by_courier = request.user
        purchase.confirmation_date = timezone.now()
        
        # Если и сотрудник подтвердил, меняем статус
        if purchase.staff_confirmed_shipping:
            purchase.status = 'shipped'
            purchase.save()
            messages.success(request, f'Статус заказа #{purchase.id} изменен на "Доставляется"')
        else:
            purchase.save()
            messages.success(request, f'Подтверждено получение заказа #{purchase.id}')
        
        return redirect('courier_orders')
    
    return render(request, 'catalog/courier/confirm_shipping.html', {'purchase': purchase})

@login_required
def confirm_delivery_courier(request, purchase_id):
    """Курьер подтверждает доставку клиенту"""
    purchase = get_object_or_404(Purchase, id=purchase_id)
    
    if not (hasattr(request.user, 'role') and request.user.role.role == 'courier'):
        messages.error(request, 'Только курьер может подтверждать доставку')
        return redirect('index')
    
    if purchase.delivery_method == 'pickup':
        messages.error(request, 'Это заказ на самовывоз')
        return redirect('courier_orders')
    
    if request.method == 'POST':
        purchase.courier_confirmed_delivery = True
        purchase.confirmed_by_courier = request.user
        purchase.confirmation_date = timezone.now()
        purchase.delivery_time = timezone.now()
        purchase.recipient_name = request.POST.get('recipient_name', '')
        purchase.notes = request.POST.get('delivery_notes', '')
        purchase.save()
        
        messages.success(request, f'Подтверждена доставка заказа #{purchase.id}')
        
        # Если и сотрудник подтвердил, завершаем доставку
        if purchase.staff_confirmed_delivery:
            purchase.status = 'delivered'
            purchase.save()
            messages.success(request, f'Заказ #{purchase.id} завершен')
        
        return redirect('courier_orders')
    
    return render(request, 'catalog/courier/confirm_delivery.html', {'purchase': purchase})

class CourierOrdersView(SimpleRoleMixin, ListView):
    model = Purchase
    template_name = 'catalog/courier/orders.html'
    context_object_name = 'orders'
    allowed_roles = ['courier', 'staff']
    
    def get_queryset(self):
        # Курьер видит только заказы на доставку
        queryset = Purchase.objects.filter(
            delivery_method__in=['krasnoyarsk', 'russia']
        ).exclude(
            status__in=['delivered', 'cancelled']
        ).order_by('-purchase_date')
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context['assembled_count'] = queryset.filter(status='assembled').count()
        context['shipped_count'] = queryset.filter(status='shipped').count()
        context['delivered_count'] = Purchase.objects.filter(
            status='delivered',
            delivery_method__in=['krasnoyarsk', 'russia']
        ).count()
        return context

class ManageBooksView(SimpleRoleMixin, ListView):
    model = Book
    template_name = 'catalog/staff/books.html'
    context_object_name = 'books'
    allowed_roles = ['staff']
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Book.objects.all().order_by('title')
        genre_id = self.request.GET.get('genre')
        if genre_id:
            queryset = queryset.filter(genre__id=genre_id)
        
        available = self.request.GET.get('available')
        if available == 'yes':
            queryset = queryset.filter(quantity__gt=0)
        elif available == 'no':
            queryset = queryset.filter(quantity=0)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['genres'] = Genre.objects.all()
        context['genre_filter'] = self.request.GET.get('genre', '')
        context['available_filter'] = self.request.GET.get('available', '')
        return context

class EditBookView(SimpleRoleMixin, UpdateView):
    model = Book
    template_name = 'catalog/staff/edit_book.html'
    fields = ['title', 'author', 'summary', 'genre', 'price', 'quantity', 'avatar']
    allowed_roles = ['staff']
    
    def form_valid(self, form):
        messages.success(self.request, f'Книга "{form.instance.title}" обновлена')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('staff_books')

class AddBookView(SimpleRoleMixin, CreateView):
    model = Book
    template_name = 'catalog/staff/add_book.html'
    fields = ['title', 'author', 'summary', 'genre', 'price', 'quantity', 'avatar']
    allowed_roles = ['staff']
    
    def form_valid(self, form):
        messages.success(self.request, f'Книга "{form.instance.title}" добавлена')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('staff_books')

class CustomerOrdersView(SimpleRoleMixin, ListView):
    model = Purchase
    template_name = 'catalog/staff/customer_orders.html'
    context_object_name = 'orders'
    allowed_roles = ['staff']
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Purchase.objects.filter(user_id=user_id).order_by('-purchase_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_id')
        context['customer'] = get_object_or_404(User, id=user_id)
        return context

class ManageNewsView(SimpleRoleMixin, ListView):
    model = News
    template_name = 'catalog/staff/news.html'
    context_object_name = 'news_list'
    allowed_roles = ['staff']
    
    def get_queryset(self):
        return News.objects.all().order_by('-published_date')

class AddNewsView(SimpleRoleMixin, CreateView):
    model = News
    template_name = 'catalog/staff/add_news.html'
    fields = ['title', 'content', 'is_published']
    allowed_roles = ['staff']
    
    def form_valid(self, form):
        messages.success(self.request, 'Новость добавлена')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('staff_news')

class EditNewsView(SimpleRoleMixin, UpdateView):
    model = News
    template_name = 'catalog/staff/edit_news.html'
    fields = ['title', 'content', 'is_published']
    allowed_roles = ['staff']
    
    def form_valid(self, form):
        messages.success(self.request, 'Новость обновлена')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('staff_news')