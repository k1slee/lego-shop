from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from django.conf import settings

from .models import Product


@dataclass(frozen=True)
class CartLine:
    product: Product
    quantity: int
    unit_price: Decimal

    @property
    def total_price(self) -> Decimal:
        return (self.unit_price * self.quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.session_key = getattr(settings, 'CART_SESSION_ID', 'cart')
        cart = self.session.get(self.session_key)
        if cart is None:
            cart = self.session[self.session_key] = {}
        self._cart = cart

    def add(self, product: Product, quantity: int, replace: bool = False) -> None:
        product_id = str(product.id)
        if product_id not in self._cart:
            self._cart[product_id] = {'quantity': 0, 'price': str(product.price)}

        if replace:
            new_quantity = quantity
        else:
            new_quantity = int(self._cart[product_id]['quantity']) + quantity

        new_quantity = max(1, new_quantity)
        if new_quantity > product.stock:
            raise ValueError('Недостаточно товара на складе')

        self._cart[product_id]['quantity'] = new_quantity
        self._cart[product_id]['price'] = str(product.price)
        self.save()

    def set(self, product: Product, quantity: int) -> None:
        if quantity <= 0:
            self.remove(product)
            return
        self.add(product, quantity=quantity, replace=True)

    def remove(self, product: Product) -> None:
        product_id = str(product.id)
        if product_id in self._cart:
            del self._cart[product_id]
            self.save()

    def clear(self) -> None:
        self.session[self.session_key] = {}
        self._cart = self.session[self.session_key]
        self.save()

    def save(self) -> None:
        self.session.modified = True

    def __len__(self) -> int:
        return sum(int(item['quantity']) for item in self._cart.values())

    def lines(self) -> Iterable[CartLine]:
        product_ids = list(self._cart.keys())
        products = Product.objects.filter(id__in=product_ids, is_active=True)
        products_by_id = {str(p.id): p for p in products}
        for product_id, item in self._cart.items():
            product = products_by_id.get(product_id)
            if product is None:
                continue
            yield CartLine(
                product=product,
                quantity=int(item['quantity']),
                unit_price=Decimal(item.get('price') or product.price),
            )

    def total_price(self) -> Decimal:
        total = Decimal('0.00')
        for line in self.lines():
            total += line.total_price
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
