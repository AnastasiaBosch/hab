from django.contrib import admin
from .models import Author, Genre, Book

#admin.site.register(Book)
#admin.site.register(Author)
admin.site.register(Genre)

# Define the admin class
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name')
admin.site.register(Author, AuthorAdmin)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'display_genre')

