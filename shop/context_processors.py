from .cart import Cart
from .models import Product


def cart_summary(request):
    cart = Cart(request)
    return {
        'cart_items_count': len(cart),
        'cart_total_price': cart.total_price(),
    }


def lego_series(request):
    series_list = Product.objects.filter(is_active=True, series__isnull=False) \
                                 .exclude(series='') \
                                 .values_list('series', flat=True) \
                                 .distinct().order_by('series')
    return {'lego_series': series_list}