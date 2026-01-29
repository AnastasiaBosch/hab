from django.urls import path
from . import views
from django.views.generic import TemplateView #отображения шаблонов без доп логики

urlpatterns = [
    path('', views.index, name='index'),
    path('books/', views.BookListView.as_view(), name='books'),
    path('book/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
    path('news/', views.NewsListView.as_view(), name='news'),
    path('news/<int:pk>/', views.NewsDetailView.as_view(), name='news-detail'),
    path('faq/', TemplateView.as_view(template_name='catalog/faq.html'), name='faq'),
]