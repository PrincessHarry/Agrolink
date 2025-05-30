from django.urls import path
from . import views
from . import webhooks
from django.contrib.auth import views as auth_views
from .views import CustomLoginView

app_name = 'link'

urlpatterns = [
    # Homepage
    path('', views.home, name='home'),
    
    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='link/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='link/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='link/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='link/password_reset_complete.html'), name='password_reset_complete'),
    
    # Profile URLs
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Product URLs
    path('products/add/', views.add_product, name='add_product'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/edit/', views.edit_product, name='edit_product'),
    path('products/<slug:slug>/delete/', views.delete_product, name='delete_product'),
    
    # Order URLs
    path('orders/create/<int:product_id>/', views.create_order, name='create_order'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/update/', views.update_order_status, name='update_order_status'),
    path('orders/<int:order_id>/tracking/', views.update_order_tracking, name='update_order_tracking'),
    path('orders/<int:order_id>/payment/', views.update_payment_status, name='update_payment_status'),
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    
    # Message URLs
    path('messages/', views.conversations, name='conversations'),
    path('messages/filter/', views.filter_messages, name='filter_messages'),
    path('messages/send/<int:receiver_id>/', views.send_message, name='send_message'),
    path('messages/<int:message_id>/archive/', views.archive_message, name='archive_message'),
    path('messages/<int:message_id>/unarchive/', views.unarchive_message, name='unarchive_message'),

    # Payment URLs
    path('order/<int:order_id>/payment/', views.initiate_payment, name='initiate_payment'),
    path('order/<int:order_id>/payment/verify/', views.verify_payment, name='payment_verify'),
    path('order/<int:order_id>/payment/status/', views.payment_status, name='payment_status'),
    path('payment/webhook/', webhooks.paystack_webhook, name='payment_webhook'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),

    # Review URLs
    path('product/<int:product_id>/review/add/', views.add_review, name='add_review'),
    path('review/<int:review_id>/edit/', views.edit_review, name='edit_review'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
] 