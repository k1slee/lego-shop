from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.conf import settings
import requests
from .models import Subscriber
from .cart import Cart
from .forms import AddToCartForm, UpdateCartForm, OrderForm
from .models import Category, Product, Order, OrderItem


def home(request):
    categories = Category.objects.filter(is_active=True).order_by('sort_order', 'name')[:8]
    featured_products = (
        Product.objects.select_related('category')
        .filter(is_active=True)
        .order_by('-created_at')[:6]
    )
    popular_products = Product.objects.filter(is_active=True).order_by('-price')[:4]
    collections = Product.objects.filter(is_active=True, series__isnull=False).exclude(series='').values_list('series', flat=True).distinct()[:6]
    return render(
        request,
        'home.html',
        {
            'categories': categories,
            'featured_products': featured_products,
            'popular_products': popular_products,
            'collections': collections,
        },
    )


def product_list(request):
    products = Product.objects.select_related('category').filter(is_active=True)
    categories = Category.objects.filter(is_active=True).order_by('sort_order', 'name')

    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    series = request.GET.get('series')
    if series:
        products = products.filter(series=series)

    q = (request.GET.get('q') or '').strip()
    if q:
        products = products.filter(Q(name__icontains=q) | Q(short_description__icontains=q))

    sort = request.GET.get('sort') or 'new'
    if sort == 'price_asc':
        products = products.order_by('price', 'name')
    elif sort == 'price_desc':
        products = products.order_by('-price', 'name')
    elif sort == 'name':
        products = products.order_by('name')
    else:
        products = products.order_by('-created_at', 'name')

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(
        request,
        'catalog/product_list.html',
        {
            'categories': categories,
            'page_obj': page_obj,
            'selected_category_slug': category_slug,
            'q': q,
            'sort': sort,
        },
    )


def product_detail(request, slug: str):
    product = get_object_or_404(Product.objects.select_related('category'), slug=slug, is_active=True)
    add_form = AddToCartForm()

    similar_products = (
        Product.objects.filter(is_active=True, category=product.category)
        .exclude(id=product.id)
        .order_by('-created_at')[:4]
    )

    return render(
        request,
        'product_detail.html',
        {
            'product': product,
            'add_form': add_form,
            'similar_products': similar_products,
        },
    )


def cart_detail(request):
    cart = Cart(request)
    lines = list(cart.lines())
    
    recommended_products = []
    if lines:
        category_ids = set(line.product.category_id for line in lines)
        cart_product_ids = [line.product.id for line in lines]
        recommended_products = Product.objects.filter(
            is_active=True,
            category_id__in=category_ids
        ).exclude(id__in=cart_product_ids).distinct()[:4]
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('cart/cart_table.html', {'lines': lines, 'cart_total': cart.total_price()}, request=request)
        return JsonResponse({
            'cart_html': html,
            'cart_items_count': len(cart),
            'cart_total_price': str(cart.total_price())
        })
    
    return render(request, 'cart/cart_detail.html', {
        'lines': lines,
        'cart_total': cart.total_price(),
        'recommended_products': recommended_products,
    })


def feedback(request):
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        message = request.POST.get('message', '')
        messages.success(request, 'Спасибо! Ваше сообщение отправлено.')
        return redirect('home')
    return redirect('home')


def cart_add(request, product_id: int):
    if request.method != 'POST':
        raise Http404

    product = get_object_or_404(Product, id=product_id, is_active=True)
    form = AddToCartForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Некорректное количество')
        return redirect(product.get_absolute_url())

    cart = Cart(request)
    try:
        cart.add(product, quantity=form.cleaned_data['quantity'], replace=False)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect(product.get_absolute_url())

    messages.success(request, 'Товар добавлен в корзину')
    return redirect('cart_detail')


def cart_update(request, product_id: int):
    if request.method != 'POST':
        raise Http404

    product = get_object_or_404(Product, id=product_id, is_active=True)
    form = UpdateCartForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Некорректное количество')
        return redirect('cart_detail')

    cart = Cart(request)
    try:
        cart.set(product, quantity=form.cleaned_data['quantity'])
    except ValueError as e:
        messages.error(request, str(e))
    else:
        messages.success(request, 'Корзина обновлена')
    return redirect('cart_detail')


def cart_remove(request, product_id: int):
    if request.method != 'POST':
        raise Http404

    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = Cart(request)
    cart.remove(product)
    messages.success(request, 'Товар удалён из корзины')
    return redirect('cart_detail')


def cart_clear(request):
    if request.method != 'POST':
        raise Http404

    cart = Cart(request)
    cart.clear()
    messages.success(request, 'Корзина очищена')
    return redirect('cart_detail')


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_success.html', {'order': order})


def checkout(request):
    cart = Cart(request)
    lines = list(cart.lines())
    
    if not lines:
        messages.error(request, 'Ваша корзина пуста. Добавьте товары перед оформлением заказа.')
        return redirect('cart_detail')
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user if request.user.is_authenticated else None
            order.total_price = cart.total_price()
            order.save()
            
            # Сохраняем позиции заказа
            for line in lines:
                OrderItem.objects.create(
                    order=order,
                    product=line.product,
                    name=line.product.name,       # поле называется name        # поле называется sku
                    price=line.unit_price,
                    quantity=line.quantity,
                    total=line.total_price
                )
            
            # Отправляем уведомление в Telegram
            send_telegram_notification(order, lines)
            
            # Очищаем корзину
            cart.clear()
            
            messages.success(request, f'Заказ №{order.id} успешно оформлен! Мы свяжемся с вами.')
            return redirect('order_success', order_id=order.id)
        else:
            messages.error(request, 'Исправьте ошибки в форме.')
    else:
        initial = {}
        if request.user.is_authenticated:
            initial['first_name'] = request.user.first_name
            initial['last_name'] = request.user.last_name
            initial['email'] = request.user.email

            if hasattr(request.user, 'profile'):
                profile = request.user.profile
                if profile.phone:
                    initial['phone'] = profile.phone
                if profile.address:
                    initial['address'] = profile.address
        form = OrderForm(initial=initial)
    
    return render(request, 'checkout.html', {
        'form': form,
        'lines': lines,
        'cart_total': cart.total_price(),
    })


def send_telegram_notification(order, lines):
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', '')
    if not bot_token or not chat_id:
        return
    
    items_text = "\n".join([
        f"• {line.product.name}  x {line.quantity} = {line.total_price} Br"
        for line in lines
    ])
    text = f"""
🆕 <b>Новый заказ #{order.id}</b>

👤 <b>Клиент:</b> {order.first_name} {order.last_name}
📞 <b>Телефон:</b> {order.phone}
📧 <b>Email:</b> {order.email}
🏠 <b>Адрес:</b> {order.address}
💬 <b>Комментарий:</b> {order.comment or '—'}

📦 <b>Состав заказа:</b>
{items_text}

💰 <b>Итого:</b> {order.total_price} Br
"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        requests.post(url, data={'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}, timeout=5)
    except Exception:
        pass

def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            obj, created = Subscriber.objects.get_or_create(email=email)
            if created:
                messages.success(request, 'Вы успешно подписались на новости!')
            else:
                messages.info(request, 'Вы уже подписаны на нашу рассылку.')
        else:
            messages.error(request, 'Введите корректный email.')
    return redirect('home')

def delivery_payment(request):
    return render(request, 'delivery_payment.html')
