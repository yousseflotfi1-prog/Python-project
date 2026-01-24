from django.contrib import admin
from .models import Category, Book, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("id", "titre", "prix", "category")
    list_filter = ("category",)
    search_fields = ("titre", "description")

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "phone", "payment_method", "total", "created_at")
    list_filter = ("payment_method", "created_at")
    inlines = [OrderItemInline]




