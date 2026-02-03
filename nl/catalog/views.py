from django.shortcuts import render, redirect,  get_object_or_404
from .models import Book, Author, Genre, News, UserProfile, Book, Purchase
from django.views import generic
from .filters import BookFilter
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from decimal import Decimal

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
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт создан для {username}! Теперь вы можете войти.')
            return redirect('login')
    else:
        form = UserCreationForm()
    
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
def make_purchase(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        payment_method = request.POST.get('payment_method', 'cash')
        
        if book.quantity < quantity:
            messages.error(request, f'Недостаточно книг на складе. Доступно: {book.quantity}')
            return redirect('book-detail', pk=book_id)
        
        profile = request.user.profile
        discount = profile.discount_percent
        
        total_price = book.price * quantity
        discount_amount = total_price * discount / 100
        final_price = total_price - discount_amount
        
        purchase = Purchase.objects.create(
            user=request.user,
            book=book,
            quantity=quantity,
            price=book.price,
            total_price=final_price,
            payment_method=payment_method
        )
        
        book.quantity -= quantity
        book.save()
        
        payment_display = 'Наличные при получении' if payment_method == 'cash' else 'Картой при получении'
        
        messages.success(
            request, 
            f'Книга "{book.title}" куплена!<br>'
            f'Сумма: {total_price} руб.<br>'
            f'Скидка: {discount}% ({discount_amount:.2f} руб.)<br>'
            f'Итог: {final_price:.2f} руб.<br>'
            f'Способ оплаты: {payment_display}'
        )
        
        return redirect('profile')
    
    return render(request, 'catalog/purchase.html', {
        'book': book,
        'user_profile': request.user.profile
    })

@login_required
def purchase_history(request):
    """История покупок пользователя"""
    purchases = Purchase.objects.filter(user=request.user).order_by('-purchase_date')
    return render(request, 'catalog/purchase_history.html', {
        'purchases': purchases,
        'total_spent': sum(p.total_price for p in purchases)
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
        unavailable_items = []
        for book_id_str, quantity in cart.items():
            book_id = int(book_id_str)
            book = get_object_or_404(Book, id=book_id)
            
            if book.quantity < quantity:
                unavailable_items.append(book.title)
        
        if unavailable_items:
            messages.error(request, f'Нет в наличии: {", ".join(unavailable_items)}')
            return redirect('cart')
        
        total_spent = 0
        for book_id_str, quantity in cart.items():
            book_id = int(book_id_str)
            book = get_object_or_404(Book, id=book_id)
            
            profile = request.user.profile
            discount = profile.discount_percent
            
            total_price = book.price * quantity
            discount_amount = total_price * discount / 100
            final_price = total_price - discount_amount
            
            Purchase.objects.create(
                user=request.user,
                book=book,
                quantity=quantity,
                price=book.price,
                total_price=final_price,
                payment_method=payment_method
            )
            

            book.quantity -= quantity
            book.save()
            
            total_spent += final_price
        
        cart_items_count = len(cart)
        request.session['cart'] = {}
        
        payment_display = 'Наличные при получении' if payment_method == 'cash' else 'Картой при получении'
        
        messages.success(
            request, 
            f'✅ Заказ оформлен!<br>'
            f'Количество товаров: {cart_items_count}<br>'
            f'Сумма: {total_spent:.2f} руб.<br>'
            f'Способ оплаты: {payment_display}<br>'
            f'Вы можете забрать заказ в магазине.'
        )
        
        return redirect('profile')
    
    total_price = 0
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
    discount_amount = total_price * discount / 100
    final_price = total_price - discount_amount
    
    return render(request, 'catalog/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'discount': discount,
        'discount_amount': discount_amount,
        'final_price': final_price
    })