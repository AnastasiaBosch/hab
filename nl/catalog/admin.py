from django.contrib import admin
from .models import Author, Genre, Book, News

#admin.site.register(Book)
#admin.site.register(Author)
admin.site.register(Genre)

# Define the admin class
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name')
admin.site.register(Author, AuthorAdmin)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'display_genre', 'price', 'quantity')
    fields = ['title', 'avatar', 'author', 'summary', 'genre', 'price', 'quantity']

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_date', 'is_published')
    list_filter = ('published_date', 'is_published')
    search_fields = ('title', 'content')
    date_hierarchy = 'published_date'
