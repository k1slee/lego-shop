from django import forms
from django.contrib import admin
from django.utils.html import mark_safe
from .models import Category, Product

# Форма для товара с чекбоксом вместо количества
class ProductForm(forms.ModelForm):
    in_stock = forms.BooleanField(label='В наличии', required=False, initial=True)

    class Meta:
        model = Product
        fields = '__all__'
        # скрываем поле stock из формы
        widgets = {
            'stock': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['in_stock'].initial = self.instance.stock > 0

    def save(self, commit=True):
        product = super().save(commit=False)
        product.stock = 1 if self.cleaned_data['in_stock'] else 0
        if commit:
            product.save()
        return product
@admin.action(description='Сделать активными')
def make_active(modeladmin, request, queryset):
    queryset.update(is_active=True)

@admin.action(description='Сделать неактивными')
def make_inactive(modeladmin, request, queryset):
    queryset.update(is_active=False)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
    list_display = ('name', 'category', 'price', 'is_active', 'created_at')  # убрали sku и stock
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'slug', 'price', 'old_price', 'in_stock', 'short_description', 'description', 'image', 'pieces', 'series', 'is_active')
        }),
    )
    actions = [make_active, make_inactive]