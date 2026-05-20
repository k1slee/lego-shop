from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    image = models.ImageField('Изображение категории', upload_to='categories/', blank=True, null=True)
    is_collection = models.BooleanField('Показывать в блоке "Коллекции" на главной', default=False)

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
    slug = models.SlugField('Slug', max_length=280, unique=True, blank=True)

    price = models.DecimalField('Цена', max_digits=12, decimal_places=2)
    old_price = models.DecimalField('Старая цена', max_digits=12, decimal_places=2, blank=True, null=True)
    in_stock = models.BooleanField('В наличии', default=True)   # исправлено на BooleanField

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
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f'{self.name}'

    def get_discount_percent(self):
        if self.old_price and self.old_price > 0:
            return int((self.old_price - self.price) / self.old_price * 100)
        return 0

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _generate_unique_slug(Product, self.name, instance_pk=self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('product_detail', kwargs={'slug': self.slug})

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменён'),
    ]
    DELIVERY_CHOICES = [
        ('courier', 'Курьер по Минску (10 Br)'),
        ('pickup', 'Самовывоз (бесплатно)'),
        ('post', 'Почта Беларуси (от 5 Br)'),
        ('europost', 'Европочта (от 7 Br)'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Пользователь')
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия', blank=True)
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(verbose_name='Email')
    address = models.TextField(verbose_name='Адрес доставки')
    comment = models.TextField(verbose_name='Комментарий к заказу', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='Статус')
    total_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Итого')
    delivery_method = models.CharField('Способ доставки', max_length=20, choices=DELIVERY_CHOICES, default='courier')
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{self.id} от {self.created_at.strftime("%d.%m.%Y")}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name='Товар')
    name = models.CharField(max_length=255, verbose_name='Название товара')  # копия на момент заказа
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Цена')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Сумма')

    def save(self, *args, **kwargs):
        self.total = self.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} x {self.quantity}'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    phone = models.CharField('Телефон', max_length=20, blank=True)
    address = models.TextField('Адрес доставки', blank=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'Профиль {self.user.username}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Subscriber(models.Model):
    email = models.EmailField('Email', unique=True)
    created_at = models.DateTimeField('Дата подписки', auto_now_add=True)

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'

    def __str__(self):
        return self.email