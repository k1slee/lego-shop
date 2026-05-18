from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .cart import Cart
from .forms import AddToCartForm, RegisterForm, UpdateCartForm
from .models import Category, Product


def home(request):
    categories = Category.objects.filter(is_active=True).order_by('sort_order', 'name')[:8]
    featured_products = (
        Product.objects.select_related('category')
        .filter(is_active=True)
        .order_by('-created_at')[:6]
    )
    return render(
        request,
        'home.html',
        {
            'categories': categories,
            'featured_products': featured_products,
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
        products = products.filter(series =series)


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
    
    # Рекомендуемые товары: из категорий товаров в корзине (до 4 штук)
    recommended_products = []
    if lines:
        # Получаем ID категорий товаров в корзине
        category_ids = set(line.product.category_id for line in lines)
        # Ищем активные товары из этих категорий, исключая уже добавленные
        cart_product_ids = [line.product.id for line in lines]
        recommended_products = Product.objects.filter(
            is_active=True,
            category_id__in=category_ids
        ).exclude(id__in=cart_product_ids).distinct()[:4]
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # AJAX-запрос – возвращаем фрагмент таблицы (если нужно)
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
        # Здесь можно отправить письмо, но для демо просто покажем сообщение
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


@login_required
def checkout_stub(request):
    return render(request, 'checkout.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('catalog')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация выполнена')
            return redirect('catalog')
        messages.error(request, 'Исправьте ошибки в форме')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})
