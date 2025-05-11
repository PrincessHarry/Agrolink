from django.contrib import admin
from .models import UserProfile, Product, Order, Message, PaymentTransaction, OrderActivity, Category, Review, OrderItem

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'phone_number', 'location')
    list_filter = ('user_type',)
    search_fields = ('user__username', 'user__email', 'phone_number', 'location')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    list_filter = ('parent',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'category', 'price', 'quantity', 'status')
    list_filter = ('status', 'category', 'seller')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'status', 'payment_status', 'total_price', 'created_at')
    list_filter = ('status', 'payment_status')
    search_fields = ('buyer__user__username', 'tracking_number')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'total_price')
    list_filter = ('order__status',)
    search_fields = ('order__id', 'product__name')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'subject', 'message_type', 'is_read', 'created_at')
    list_filter = ('message_type', 'is_read', 'is_archived')
    search_fields = ('subject', 'content', 'sender__user__username', 'receiver__user__username')
    readonly_fields = ('created_at', 'read_at')

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'order', 'amount', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('reference', 'order__id')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('product__name', 'user__user__username', 'comment')
    readonly_fields = ('created_at', 'updated_at')
