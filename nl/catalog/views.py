from django.shortcuts import render, redirect,  get_object_or_404, reverse
from .models import Book, Author, Genre, News, UserProfile, Book, Purchase
from django.views import generic
from .filters import BookFilter
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User 
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from decimal import Decimal
from .mixins import SimpleRoleMixin
from django.views.generic import ListView, UpdateView, CreateView, TemplateView
from django.db.models import Sum, Count
import datetime

def index(request):
    """
    Функция отображения для домашней страницы сайта.
    """
    num_books=Book.objects.all().count()
    num_authors=Author.objects.count()  # Метод 'all()' применён по умолчанию.
    num_genres = Genre.objects.count()
    num_news = News.objects.filter(is_published=True).count()

    news_list = News.objects.filter(is_published=True).order_by('-published_date')[:5]
     
    # Отрисовка HTML-шаблона index.html с данными внутри
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
        genre_id = self.request.GET.get('genre')
        if genre_id:
            queryset = queryset.filter(genre__id=genre_id)
            
        is_available = self.request.GET.get('is_available')
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
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, 'Пароли не совпадают')
            return render(request, 'catalog/registration/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким email уже существует')
            return render(request, 'catalog/registration/register.html')
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            
            UserProfile.objects.create(user=user)
            
            messages.success(
                request, 
                f'Аккаунт создан для {username}! Теперь вы можете войти.'
            )
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'Ошибка при создании пользователя: {str(e)}')
            return render(request, 'catalog/registration/register.html')
    
    # Если GET запрос
    return render(request, 'catalog/registration/register.html')

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

# @login_required
# def make_purchase(request, book_id):
#     """Покупка одной книги (без корзины)"""
#     book = get_object_or_404(Book, id=book_id)
 #   
#     if request.method == 'POST':
#         quantity = int(request.POST.get('quantity', 1))
#         payment_method = request.POST.get('payment_method', 'cash')
#         delivery_method = request.POST.get('delivery_method', 'pickup')
        
#         if book.quantity < quantity:
#             messages.error(request, f'Недостаточно книг на складе. Доступно: {book.quantity}')
#             return redirect('book-detail', pk=book_id)
#        
#         profile = request.user.profile
#         discount = profile.discount_percent
#        
#         total_price = book.price * quantity
#         discount_amount = total_price * discount / 100
#        
#         if delivery_method == 'pickup':
#             delivery_cost = 0
#         elif delivery_method == 'krasnoyarsk':
#             delivery_cost = 400
#         elif delivery_method == 'russia':
#             # 250 за первую книгу, +50 за каждую следующую
#             delivery_cost = 250 + (max(0, quantity - 1) * 50)
#         else:
#             delivery_cost = 0
#         final_price = total_price - discount_amount + delivery_cost
#        
#         purchase = Purchase.objects.create(
#             user=request.user,
#             book=book,
#             quantity=quantity,
#             price=book.price,
#             total_price=total_price - discount_amount,
#             payment_method=payment_method,
#             delivery_method=delivery_method,
#             delivery_cost=delivery_cost
#         )
        
#         # Уменьшаем количество книг на складе
#         book.quantity -= quantity
#         book.save()
        
#         # Определяем отображаемое название способа оплаты
#         payment_display = 'Наличные при получении' if payment_method == 'cash' else 'Картой при получении'
        
#         # Определяем отображаемое название способа доставки
#         delivery_display = {
#             'pickup': 'Самовывоз (бесплатно)',
#             'krasnoyarsk': 'Доставка по Красноярску (400 ₽)',
#             'russia': f'Доставка по России ({delivery_cost} ₽)',
#         }.get(delivery_method, 'Не указано')
        
#         messages.success(
#             request, 
#             f'Книга "{book.title}" куплена!<br>'
#             f'Сумма: {total_price} руб.<br>'
#             f'Скидка: {discount}% ({discount_amount:.2f} руб.)<br>'
#             f'Доставка: {delivery_cost} руб.<br>'
#             f'Итог: {final_price:.2f} руб.<br>'
#             f'Способ оплаты: {payment_display}<br>'
#             f'Способ доставки: {delivery_display}'
#         )
        
#         return redirect('profile')
    
#     # Если GET запрос, показываем страницу оформления
#     return render(request, 'catalog/purchase.html', {
#         'book': book,
#         'user_profile': request.user.profile
#     })

@login_required
def purchase_history(request):
    """История покупок пользователя"""
    purchases = Purchase.objects.filter(user=request.user).order_by('-purchase_date')
    total_spent = sum(p.total_price for p in purchases)
    
    return render(request, 'catalog/purchase_history.html', {
        'purchases': purchases,
        'total_spent': total_spent,
    })

def cart_view(request):
    """Просмотр корзины"""
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
    """Добавить книгу в корзину"""
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
    """Изменить количество книги в корзине"""
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
    """Очистить всю корзину"""
    request.session['cart'] = {}
    messages.success(request, 'Корзина очищена')
    return redirect('cart')

@login_required
def checkout(request):
    """Оформить заказ"""
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
        cart_items = []
        
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
        
        profile = request.user.profile
        discount = profile.discount_percent
        
        if delivery_method == 'pickup':
            delivery_cost = Decimal('0')
        elif delivery_method == 'krasnoyarsk':
            delivery_cost = Decimal('400')
        elif delivery_method == 'russia':
            delivery_cost = Decimal('250') + (max(0, total_books - 1) * Decimal('50'))
        else:
            delivery_cost = Decimal('0')
        
        discount_amount = total_price * Decimal(discount) / Decimal('100')
        final_price = total_price - discount_amount + delivery_cost
        
        total_spent = Decimal('0')
        for book_id_str, quantity in cart.items():
            book_id = int(book_id_str)
            book = get_object_or_404(Book, id=book_id)
        
            item_total = book.price * quantity
            item_discount = item_total * Decimal(discount) / Decimal('100')
            item_final_price = item_total - item_discount
            
            item_delivery_cost = (Decimal(quantity) / Decimal(total_books)) * delivery_cost if total_books > 0 else Decimal('0')
            
            Purchase.objects.create(
                user=request.user,
                book=book,
                quantity=quantity,
                price=book.price,
                total_price=item_final_price,
                payment_method=payment_method,
                delivery_method=delivery_method,
                delivery_cost=item_delivery_cost,
                status='created'  
            )
            book.quantity -= quantity
            book.save()
            
            total_spent += item_final_price + item_delivery_cost
        
        cart_items_count = len(cart)
        request.session['cart'] = {}

        payment_display = 'Наличные при получении' if payment_method == 'cash' else 'Картой при получении'

        delivery_display = {
            'pickup': 'Самовывоз (бесплатно)',
            'krasnoyarsk': 'Доставка по Красноярску (400 ₽)',
            'russia': f'Доставка по России ({delivery_cost} ₽)',
        }.get(delivery_method, 'Не указано')
        
        messages.success(
            request, 
            f'✅ Заказ оформлен! Статус: 🟡 Создан<br>'
            f'Количество товаров: {cart_items_count}<br>'
            f'Товары: {total_price} руб.<br>'
            f'Скидка: {discount}% ({discount_amount:.2f} руб.)<br>'
            f'Доставка: {delivery_cost} руб.<br>'
            f'Итог: {final_price:.2f} руб.<br>'
            f'Способ оплаты: {payment_display}<br>'
            f'Способ доставки: {delivery_display}<br>'
            f'Вы можете забрать заказ в магазине.'
        )
        
        return redirect('profile')
    
    # Если GET запрос, показываем страницу оформления заказа
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
    """Главная панель сотрудника"""
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
            'today_revenue': sum(o.total_price for o in today_orders),
            'low_stock': low_stock,
            'total_books': Book.objects.count(),
            'active_orders': Purchase.objects.exclude(
                status__in=['delivered', 'cancelled']
            ).count(),
        })
        
        return context

class ManageOrdersView(SimpleRoleMixin, ListView):
    """Управление заказами"""
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

class UpdateOrderStatusView(SimpleRoleMixin, UpdateView):
    """Изменение статуса заказа (для сотрудника)"""
    model = Purchase
    template_name = 'catalog/staff/update_order_status.html'
    fields = ['status']
    allowed_roles = ['staff']
    
    def form_valid(self, form):
        form.instance.status_changed_by = self.request.user
        messages.success(self.request, f'Статус заказа #{self.object.id} обновлен')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('staff_orders')

class ManageBooksView(SimpleRoleMixin, ListView):
    """Управление книгами"""
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
    """Редактирование книги"""
    model = Book
    template_name = 'catalog/staff/edit_book.html'
    fields = ['title', 'author', 'summary', 'genre', 'price', 'quantity']
    allowed_roles = ['staff']
    
    def form_valid(self, form):
        form.instance.last_updated_by = self.request.user
        messages.success(self.request, f'Книга "{form.instance.title}" обновлена')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('staff_books')

class AddBookView(SimpleRoleMixin, CreateView):
    """Добавление новой книги"""
    model = Book
    template_name = 'catalog/staff/add_book.html'
    fields = ['title', 'author', 'summary', 'genre', 'price', 'quantity', 'avatar']
    allowed_roles = ['staff']
    
    def form_valid(self, form):
        form.instance.last_updated_by = self.request.user
        messages.success(self.request, f'Книга "{form.instance.title}" добавлена')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('staff_books')

class CustomerOrdersView(SimpleRoleMixin, ListView):
    """Заказы конкретного покупателя"""
    model = Purchase
    template_name = 'catalog/staff/customer_orders.html'
    allowed_roles = ['staff']
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Purchase.objects.filter(user_id=user_id).order_by('-purchase_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_id')
        context['customer'] = User.objects.get(id=user_id)
        return context

class CourierOrdersView(SimpleRoleMixin, ListView):
    """Заказы для курьера - только те, что нужно доставлять"""
    model = Purchase
    template_name = 'catalog/courier/orders.html'
    context_object_name = 'orders'
    allowed_roles = ['courier', 'staff']
    
    def get_queryset(self):
        return Purchase.objects.filter(
            status__in=['assembled', 'shipped'],
            delivery_method__in=['krasnoyarsk', 'russia']
        ).order_by('-purchase_date')

class CourierUpdateStatusView(SimpleRoleMixin, UpdateView):
    """Курьер меняет статус доставки"""
    model = Purchase
    template_name = 'catalog/courier/update_status.html'
    fields = ['status']
    allowed_roles = ['courier', 'staff'] 
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        status_choices = []
        
        if self.object.status == 'assembled':
            status_choices = [('shipped', '🔵 Доставляется')]
        elif self.object.status == 'shipped':
            status_choices = [('delivered', '🟢 Доставлен')]
        
        form.fields['status'].choices = status_choices
        return form
    
    def form_valid(self, form):
        old_status = self.object.status
        response = super().form_valid(form)

        if form.instance.status == 'delivered' and old_status != 'delivered':
            form.instance.book.sold_count += form.instance.quantity
            form.instance.book.save()
            messages.success(self.request, f'✅ Книга "{form.instance.book.title}" отмечена как доставленная')
        
        messages.success(self.request, f'Статус заказа #{self.object.id} обновлен')
        return response
    
    def get_success_url(self):
        return reverse('courier_orders')

class ManageNewsView(SimpleRoleMixin, ListView):
    """Управление новостями"""
    model = News
    template_name = 'catalog/staff/news.html'
    context_object_name = 'news_list'
    allowed_roles = ['staff']
    
    def get_queryset(self):
        return News.objects.all().order_by('-published_date')

class AddNewsView(SimpleRoleMixin, CreateView):
    """Добавление новости"""
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
    """Редактирование новости"""
    model = News
    template_name = 'catalog/staff/edit_news.html'
    fields = ['title', 'content', 'is_published']
    allowed_roles = ['staff']
    
    def form_valid(self, form):
        messages.success(self.request, 'Новость обновлена')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('staff_news')
    