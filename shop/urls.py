from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.product_list, name='catalog'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html', authentication_form=LoginForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/clear/', views.cart_clear, name='cart_clear'),
    path('checkout/', views.checkout, name='checkout'),
    path('register/', views.register, name='register'),
    path('feedback/', views.feedback, name='feedback'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('profile/', views.profile_dashboard, name='profile_dashboard'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/orders/', views.order_history, name='order_history'),
    path('profile/order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('subscribe/', views.subscribe, name='subscribe'),
]
