from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from shop.models import Category, Product


class Command(BaseCommand):
    help = 'Загружает демо-категории и товары'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Удалить текущие демо-товары/категории и создать заново')

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reset']:
            Product.objects.all().delete()
            Category.objects.all().delete()

        categories = [
            ('City', 'Город и спецслужбы'),
            ('Technic', 'Техника и механика'),
            ('Star Wars', 'Вселенная Star Wars'),
        ]

        created_categories = []
        for name, description in categories:
            cat, _ = Category.objects.get_or_create(
                name=name,
                defaults={'description': description, 'is_active': True, 'sort_order': 0},
            )
            created_categories.append(cat)

        products = [
            {
                'name': 'LEGO City Полицейский участок',
                'category': created_categories[0],
                'sku': 'CITY-001',
                'price': Decimal('7999.00'),
                'old_price': Decimal('8999.00'),
                'stock': 10,
                'short_description': 'Большой набор с полицейским участком и транспортом.',
                'description': 'Демо-описание. Добавьте реальный текст и изображение через админку.',
                'age_group': '6+',
                'pieces': 743,
                'series': 'City',
            },
            {
                'name': 'LEGO Technic Гоночный болид',
                'category': created_categories[1],
                'sku': 'TECH-002',
                'price': Decimal('12999.00'),
                'old_price': None,
                'stock': 5,
                'short_description': 'Модель с детализацией и интересными механизмами.',
                'description': 'Демо-описание. Добавьте реальный текст и изображение через админку.',
                'age_group': '10+',
                'pieces': 1284,
                'series': 'Technic',
            },
            {
                'name': 'LEGO Star Wars Истребитель',
                'category': created_categories[2],
                'sku': 'SW-003',
                'price': Decimal('9999.00'),
                'old_price': Decimal('10999.00'),
                'stock': 0,
                'short_description': 'Коллекционная модель для фанатов Star Wars.',
                'description': 'Демо-описание. Добавьте реальный текст и изображение через админку.',
                'age_group': '9+',
                'pieces': 589,
                'series': 'Star Wars',
            },
        ]

        created_products = 0
        for data in products:
            _, created = Product.objects.get_or_create(sku=data['sku'], defaults=data)
            created_products += int(created)

        self.stdout.write(self.style.SUCCESS(f'Готово. Категорий: {Category.objects.count()}, товаров: {Product.objects.count()} (добавлено: {created_products})'))
