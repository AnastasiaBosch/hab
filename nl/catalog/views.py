from django.shortcuts import render
from .models import Book, Author, Genre, News
from django.views import generic

def index(request):
    """
    Функция отображения для домашней страницы сайта.
    """
    # Генерация "количеств" некоторых главных объектов
    num_books=Book.objects.all().count()
    num_authors=Author.objects.count()  # Метод 'all()' применён по умолчанию.
    num_genres = Genre.objects.count()
    num_news = News.objects.filter(is_published=True).count()
    
    # Последние 5 новостей
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
    
class BookDetailView(generic.DetailView):
    model = Book

# Добавим представление для списка всех новостей
class NewsListView(generic.ListView):
    model = News
    template_name = 'catalog/news_list.html'
    paginate_by = 10
    
    def get_queryset(self):
        return News.objects.filter(is_published=True).order_by('-published_date')

# Добавим представление для детального просмотра новости
class NewsDetailView(generic.DetailView):
    model = News
    template_name = 'catalog/news_detail.html'
    
    def get_queryset(self):
        return News.objects.filter(is_published=True)