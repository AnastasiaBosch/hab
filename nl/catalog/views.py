from django.shortcuts import render
from .models import Book, Author, Genre, News
from django.views import generic
from .filters import BookFilter
from django.db.models import Q

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

# все новости
class NewsListView(generic.ListView):
    model = News
    template_name = 'catalog/news_list.html'
    paginate_by = 10
    
    def get_queryset(self):
        return News.objects.filter(is_published=True).order_by('-published_date')

#детальный просмотр
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