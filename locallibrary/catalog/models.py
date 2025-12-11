from django.db import models
from django.urls import reverse
from django.conf import settings
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
import uuid  # Требуется для уникальных экземпляров книг
from django.core.exceptions import ValidationError


class Genre(models.Model):
    """
    Модель, представляющая жанр книги (например, научная фантастика, документальная литература).
    """
    name = models.CharField(max_length=200, help_text="Укажите жанр книги (например, научная фантастика, французская поэзия и т. д.)")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Genres"
        verbose_name = "Genre"


class Language(models.Model):
    """Model representing a Language (e.g. English, French, Japanese, etc.)"""
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        """String for representing the Model object (in Admin site etc.)"""
        return self.name

    class Meta:
        constraints = [
            UniqueConstraint(
                Lower('name'),
                name='language_name_case_insensitive_unique',
                violation_error_message="Language already exists (case insensitive match)"
            ),
        ]


class Author(models.Model):
    """
    Модель, представляющая автора.
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField('Died', null=True, blank=True)

    def get_absolute_url(self):
        """
        Возвращает URL-адрес для доступа к конкретному экземпляру автора.
        """
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        """
        Строка для представления объекта модели.
        """
        return f'{self.last_name}, {self.first_name}'

    class Meta:
        ordering = ['last_name']


class Book(models.Model):
    """
    Модель, представляющая книгу (но не конкретный экземпляр книги).
    """
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, related_name='books')
    data_added = models.DateField(null=True, blank=True)
    summary = models.TextField(max_length=1000, help_text="Введите краткое описание книги")
    isbn = models.CharField(
        'ISBN',
        max_length=13,
        help_text='13 characters <a href="https://www.isbn-international.org/content/what-isbn">ISBN номер</a>'
    )
    genre = models.ManyToManyField('Genre', help_text="Выберите жанр этой книги")
    language = models.ForeignKey('Language', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """
        Возвращает URL-адрес для доступа к определенному экземпляру книги.
        """
        return reverse('book-detail', args=[str(self.id)])

    def display_genre(self):
        """
        Создает строку для жанра. Это необходимо для отображения жанра в администраторе.
        """
        return ', '.join(genre.name for genre in self.genre.all()[:3])

    display_genre.short_description = 'Genre'

    def clean(self):
        if self.author and self.data_added and self.author.date_of_birth:
            if self.data_added < self.author.date_of_birth:
                raise ValidationError('Дата добавления книги не может быть раньше даты рождения автора.')

    class Meta:
        verbose_name_plural = "Books"
        verbose_name = "Book"


class BookInstance(models.Model):
    """
    Модель, представляющая конкретный экземпляр книги (т. е. её можно взять в библиотеке).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text="Уникальный идентификатор этой конкретной книги во всей библиотеке")
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True)
    imprint = models.CharField(max_length=200)
    due_back = models.DateField(null=True, blank=True)
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    LOAN_STATUS = (
        ('m', 'Maintenance'),
        ('o', 'On loan'),
        ('a', 'Available'),
        ('r', 'Reserved'),
    )
    status = models.CharField(
        max_length=1,
        choices=LOAN_STATUS,
        blank=True,
        default='m',
        help_text='Статус наличия книги'
    )

    class Meta:
        ordering = ["due_back"]
        permissions = [("can_mark_returned", "Set book as returned")]

    def __str__(self):
        return f'{self.id} ({self.book.title})'