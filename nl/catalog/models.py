from django.db import models
from django.urls import reverse

class Genre(models.Model):

    name = models.CharField(max_length=200, help_text="Укажите жанр книги (например, научная фантастика, французская поэзия и т.д.)")

    def __str__(self):
        """
        String for representing the Model object (in Admin site etc.)
        """
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True)
    summary = models.TextField(max_length=1000, help_text="Введите краткое описание книги")
    genre = models.ManyToManyField(Genre, help_text="Select a genre for this book")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена", default=0)
    quantity = models.PositiveIntegerField(default=0, verbose_name="Количество на складе")
    
    class Meta:
        ordering = ['title']
        
    def __str__(self):
        """
        String for representing the Model object.
        """
        return self.title

    @property
    def is_available(self):
        """Проверка"""
        return self.quantity > 0
    
    def reduce_quantity(self, amount=1):
        """Уменьшает"""
        if self.quantity >= amount:
            self.quantity -= amount
            self.save()
            return True
        return False
    
    def increase_quantity(self, amount=1):
        """Увеличивает"""
        self.quantity += amount
        self.save()

    def get_absolute_url(self):
        """
        Returns the url to access a particular book instance.
        """
        return reverse('book-detail', args=[str(self.id)])

    def display_genre(self):
        """
        Creates a string for the Genre. This is required to display genre in Admin.
        """
        return ', '.join([ genre.name for genre in self.genre.all()[:3] ])
    display_genre.short_description = 'Genre'
    
class Author(models.Model):
    """
    Model representing an author.
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def get_absolute_url(self):
        """
        Returns the url to access a particular author instance.
        """
        return reverse('author-detail', args=[str(self.id)])


    def __str__(self):
        """
        String for representing the Model object.
        """
        return '%s, %s' % (self.last_name, self.first_name)

class News(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок новости")
    content = models.TextField(verbose_name="Содержание новости")
    published_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    
    class Meta:
        ordering = ['-published_date']
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
    
    def __str__(self):
        return self.title