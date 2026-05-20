from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.product_list, name='catalog'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/clear/', views.cart_clear, name='cart_clear'),
    path('checkout/', views.checkout, name='checkout'),
    path('feedback/', views.feedback, name='feedback'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('delivery-payment/', views.delivery_payment, name='delivery_payment'),
]
