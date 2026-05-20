from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'phone', 'email', 'address', 'delivery_method', 'comment']
        fields = ['first_name', 'last_name', 'phone', 'email', 'address', 'delivery_method', 'comment']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иван'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+375 (29) 123-45-67'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ivan@example.com'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Город, улица, дом, квартира'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Пожелания по доставке...'}),
            'delivery_method': forms.Select(attrs={'class': 'form-control'}),
        }
        
class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(
        label='Количество',
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
    )


class UpdateCartForm(forms.Form):
    quantity = forms.IntegerField(
        label='Количество',
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': '0'}),
    )
