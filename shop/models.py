from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def _generate_unique_slug(model_cls, base: str, *, instance_pk=None) -> str:
    base_slug = slugify(base) or 'item'
    slug = base_slug
    counter = 2
    qs = model_cls.objects.all()
    if instance_pk is not None:
        qs = qs.exclude(pk=instance_pk)
    while qs.filter(slug=slug).exists():
        slug = f'{base_slug}-{counter}'
        counter += 1
    return slug


class Category(models.Model):
    name = models.CharField('Название', max_length=200, unique=True)
    slug = models.SlugField('Slug', max_length=220, unique=True, blank=True)
    description = models.TextField('Описание', blank=True)
    sort_order = models.PositiveIntegerField('Порядок сортировки', default=0)
    is_active = models.BooleanField('Активна', default=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['sort_order', 'name']

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _generate_unique_slug(Category, self.name, instance_pk=self.pk)
        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField('Название', max_length=255)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='Категория',
    )
    sku = models.CharField('Артикул', max_length=64, unique=True)
    slug = models.SlugField('Slug', max_length=280, unique=True, blank=True)

    price = models.DecimalField('Цена', max_digits=12, decimal_places=2)
    old_price = models.DecimalField('Старая цена', max_digits=12, decimal_places=2, blank=True, null=True)
    stock = models.PositiveIntegerField('Количество на складе', default=0)

    short_description = models.TextField('Краткое описание')
    description = models.TextField('Полное описание')
    image = models.ImageField('Изображение', upload_to='products/', blank=True, null=True)

    age_group = models.CharField('Возрастная группа', max_length=50, blank=True)
    pieces = models.PositiveIntegerField('Количество деталей', blank=True, null=True)
    series = models.CharField('Серия', max_length=100, blank=True)

    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at', 'name']
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['sku']),
            models.Index(fields=['slug']),
        ]

    def __str__(self) -> str:
        return f'{self.name} ({self.sku})'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _generate_unique_slug(Product, self.name, instance_pk=self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})
