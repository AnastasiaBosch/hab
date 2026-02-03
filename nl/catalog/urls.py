from django.urls import path
from . import views
from django.views.generic import TemplateView #отображения шаблонов без доп логики
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('books/', views.BookListView.as_view(), name='books'),
    path('book/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
    path('news/', views.NewsListView.as_view(), name='news'),
    path('news/<int:pk>/', views.NewsDetailView.as_view(), name='news-detail'),
    path('faq/', TemplateView.as_view(template_name='catalog/faq.html'), name='faq'),
    path('authors/', views.AuthorListView.as_view(), name='authors'), 
    path('author/<int:pk>/', views.AuthorDetailView.as_view(), name='author-detail'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='catalog/registration/login.html'), name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/profile/', views.profile, name='profile'),
    path('purchase/<int:book_id>/', views.make_purchase, name='make_purchase'),
    path('accounts/purchase_history/', views.purchase_history, name='purchase_history'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:book_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:book_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/checkout/', views.checkout, name='checkout'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)