from django.contrib import admin

from .models import Category, Product
from django.utils.html import mark_safe

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_preview', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    fields = ('name', 'slug', 'image', 'description', 'sort_order', 'is_active')
    
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 50px; border-radius: 4px;">')
        return '-'
    image_preview.short_description = 'Превью'


@admin.action(description='Сделать активными')
def make_active(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description='Сделать неактивными')
def make_inactive(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'price', 'stock', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    actions = [make_active, make_inactive]
