from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q, Avg, Count
from datetime import datetime
from .models import UserProfile, Product, Order, Message, PaymentTransaction, OrderActivity, Category, Review, Conversation, OrderItem
from .forms import UserRegistrationForm, UserProfileForm, ProductForm, MessageForm, ReviewForm
from django.contrib.auth.models import User
from .consumers import send_notification
from django.core.paginator import Paginator
from .paystack import PaystackAPI, create_payment_transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models.functions import Coalesce

# Homepage View
def home(request):
    featured_products = Product.objects.filter(is_available=True).order_by('-created_at')[:6]
    context = {
        'featured_products': featured_products,
    }
    return render(request, 'link/home.html', context)

# User Registration View
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'link/register.html', {'form': form})

# User Profile Views
@login_required
def profile(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None
    return render(request, 'link/profile.html', {'profile': profile})

@login_required
def edit_profile(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('link:profile')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'link/edit_profile.html', {'form': form})

# Product Views
@login_required
def product_list(request):
    # Get all products
    products = Product.objects.all()
    categories = Category.objects.all()

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    # Category filter
    category_ids = request.GET.getlist('category')
    if category_ids:
        products = products.filter(category_id__in=category_ids)

    # Price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Status filter
    status = request.GET.get('status')
    if status:
        products = products.filter(status=status)

    # Payment status filter
    payment_status = request.GET.get('payment_status')
    if payment_status:
        products = products.filter(payment_status=payment_status)

    # Sorting
    sort = request.GET.get('sort', 'newest')
    if sort == 'newest':
        products = products.order_by('-created_at')
    elif sort == 'oldest':
        products = products.order_by('created_at')
    elif sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'name_asc':
        products = products.order_by('name')
    elif sort == 'name_desc':
        products = products.order_by('-name')

    # Add rating and review count
    products = products.annotate(
        rating=Coalesce(Avg('reviews__rating'), 0.0),
        review_count=Count('reviews')
    )

    # Pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'link/product_list.html', context)

@login_required
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    related_products = Product.objects.filter(
        category=product.category,
        is_available=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'link/product_detail.html', context)

@login_required
def add_product(request):
    if request.user.userprofile.user_type != 'farmer':
        messages.error(request, 'Only farmers can add products.')
        return redirect('link:product_list')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.farmer = request.user.userprofile
            product.save()
            messages.success(request, 'Product added successfully.')
            return redirect('link:product_detail', slug=product.slug)
    else:
        form = ProductForm()
    
    return render(request, 'link/add_product.html', {'form': form})

@login_required
def edit_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.user.userprofile != product.farmer:
        messages.error(request, 'You can only edit your own products.')
        return redirect('link:product_list')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('link:product_detail', slug=product.slug)
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'link/edit_product.html', {'form': form, 'product': product})

@login_required
def delete_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.user.userprofile != product.farmer:
        messages.error(request, 'You can only delete your own products.')
        return redirect('link:product_list')
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully.')
        return redirect('link:product_list')
    
    return render(request, 'link/delete_product.html', {'product': product})

# Order Views
@login_required
def order_list(request):
    # Get base queryset based on user type
    if request.user.userprofile.user_type == 'farmer':
        orders = Order.objects.filter(product__farmer=request.user.userprofile)
    else:
        orders = Order.objects.filter(buyer=request.user.userprofile)
    
    # Apply filters
    status = request.GET.get('status')
    payment_status = request.GET.get('payment_status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if status:
        orders = orders.filter(status=status)
    if payment_status:
        orders = orders.filter(payment_status=payment_status)
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(orders, 10)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    
    context = {
        'orders': orders,
        'status_choices': dict(Order.STATUS_CHOICES),
        'payment_status_choices': dict(Order.PAYMENT_STATUS_CHOICES),
        'current_status': status,
        'current_payment_status': payment_status,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'link/order_list.html', context)

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user has permission to view this order
    if request.user.userprofile not in [order.buyer, order.product.farmer]:
        messages.error(request, 'You do not have permission to view this order.')
        return redirect('link:order_list')
    
    context = {
        'order': order,
        'status_choices': dict(Order.STATUS_CHOICES),
    }
    return render(request, 'link/order_detail.html', context)

@login_required
def create_order(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.userprofile.user_type != 'buyer':
        messages.error(request, 'Only buyers can place orders.')
        return redirect('link:product_detail', slug=product.slug)
    
    if request.method == 'POST':
        quantity = float(request.POST.get('quantity', 0))
        if quantity <= 0:
            messages.error(request, 'Please enter a valid quantity.')
            return redirect('link:product_detail', slug=product.slug)
        
        if quantity > product.quantity:
            messages.error(request, 'Requested quantity not available.')
            return redirect('link:product_detail', slug=product.slug)
        
        total_price = product.price * quantity
        
        # Create the order
        order = Order.objects.create(
            buyer=request.user.userprofile,
            total_price=total_price,
            shipping_address=request.user.userprofile.address
        )
        
        # Create the order item
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price
        )
        
        # Update product quantity
        product.quantity -= quantity
        product.save()
        
        messages.success(request, 'Order placed successfully!')
        return redirect('link:order_list')
    
    return render(request, 'link/create_order.html', {'product': product})

@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user is the farmer who owns the product
    if request.user.userprofile != order.product.farmer:
        messages.error(request, 'You do not have permission to update this order.')
        return redirect('link:order_list')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            
            # Calculate delivery date if order is shipped
            if new_status == 'shipped':
                order.calculate_delivery_date()
            
            messages.success(request, f'Order status updated to {order.get_status_display()}')
        else:
            messages.error(request, 'Invalid status provided.')
    
    return redirect('link:order_detail', order_id=order.id)

@login_required
def update_payment_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user is the farmer who owns the product
    if request.user.userprofile != order.product.farmer:
        messages.error(request, 'You do not have permission to update this order.')
        return redirect('link:order_list')
    
    if request.method == 'POST':
        new_status = request.POST.get('payment_status')
        if new_status in dict(Order.PAYMENT_STATUS_CHOICES):
            order.update_payment_status(new_status)
            messages.success(request, f'Payment status updated to {order.get_payment_status_display()}')
        else:
            messages.error(request, 'Invalid payment status provided.')
    
    return redirect('link:order_detail', order_id=order.id)

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user is the buyer
    if request.user.userprofile != order.buyer:
        messages.error(request, 'You do not have permission to cancel this order.')
        return redirect('link:order_list')
    
    if order.status != 'pending':
        messages.error(request, 'Only pending orders can be cancelled.')
        return redirect('link:order_detail', order_id=order.id)
    
    if request.method == 'POST':
        # Restore product quantity
        product = order.product
        product.quantity += order.quantity
        product.save()
        
        # Update order status
        order.status = 'cancelled'
        order.save()
        
        messages.success(request, 'Order cancelled successfully.')
        return redirect('link:order_list')
    
    return render(request, 'link/cancel_order.html', {'order': order})

@login_required
def update_order_tracking(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user is the farmer who owns the product
    if request.user.userprofile != order.product.farmer:
        messages.error(request, 'You do not have permission to update this order.')
        return redirect('link:order_list')
    
    if request.method == 'POST':
        tracking_number = request.POST.get('tracking_number')
        notes = request.POST.get('notes')
        
        if tracking_number:
            order.tracking_number = tracking_number
            order.status = 'shipped'
            order.calculate_delivery_date()
        
        if notes:
            order.notes = notes
        
        order.save()
        messages.success(request, 'Order tracking information updated successfully.')
    
    return redirect('link:order_detail', order_id=order.id)

# Message Views
@login_required
def message_list(request):
    messages = Message.objects.filter(
        Q(sender=request.user.userprofile) |
        Q(receiver=request.user.userprofile)
    ).order_by('-created_at')
    return render(request, 'link/message_list.html', {'messages': messages})

@login_required
def send_message(request, receiver_id):
    receiver = get_object_or_404(UserProfile, id=receiver_id)
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user.userprofile
            message.receiver = receiver
            message.save()
            
            # Send notification to receiver
            send_notification(
                receiver.user.id,
                'new_message',
                f'New message from {request.user.username}',
                {
                    'message_id': message.id,
                    'sender': request.user.username,
                    'content': message.content[:50] + '...' if len(message.content) > 50 else message.content,
                    'type': message.message_type
                }
            )
            
            messages.success(request, 'Message sent successfully!')
            return redirect('link:conversations')
    else:
        form = MessageForm()
    
    context = {
        'form': form,
        'receiver': receiver,
        'message_types': Message.MESSAGE_TYPES
    }
    return render(request, 'link/send_message.html', context)

@login_required
def conversations(request):
    # Get all unique conversations for the current user
    sent_messages = Message.objects.filter(sender=request.user.userprofile).values('receiver').distinct()
    received_messages = Message.objects.filter(receiver=request.user.userprofile).values('sender').distinct()
    
    # Combine and get unique user IDs
    user_ids = set()
    for msg in sent_messages:
        user_ids.add(msg['receiver'])
    for msg in received_messages:
        user_ids.add(msg['sender'])
    
    # Get the conversations with the latest message
    conversations = []
    for user_id in user_ids:
        other_user = UserProfile.objects.get(id=user_id)
        last_message = Message.objects.filter(
            (Q(sender=request.user.userprofile) & Q(receiver=other_user)) |
            (Q(sender=other_user) & Q(receiver=request.user.userprofile))
        ).order_by('-created_at').first()
        
        unread_count = Message.objects.filter(
            sender=other_user,
            receiver=request.user.userprofile,
            is_read=False
        ).count()
        
        conversations.append({
            'other_user': other_user.user,
            'last_message': last_message,
            'unread_count': unread_count
        })
    
    # Sort conversations by last message time
    conversations.sort(key=lambda x: x['last_message'].created_at if x['last_message'] else datetime.min, reverse=True)
    
    # Get selected conversation if any
    selected_conversation_id = request.GET.get('conversation')
    selected_conversation = None
    messages = []
    
    if selected_conversation_id:
        other_user = User.objects.get(id=selected_conversation_id)
        messages = Message.objects.filter(
            (Q(sender=request.user.userprofile) & Q(receiver__user=other_user)) |
            (Q(sender__user=other_user) & Q(receiver=request.user.userprofile))
        ).order_by('created_at')
        
        # Mark messages as read
        Message.objects.filter(
            sender__user=other_user,
            receiver=request.user.userprofile,
            is_read=False
        ).update(is_read=True)
        
        selected_conversation = {
            'other_user': other_user,
            'messages': messages
        }
    
    context = {
        'conversations': conversations,
        'selected_conversation': selected_conversation,
        'messages': messages,
        'message_types': Message.MESSAGE_TYPES
    }
    return render(request, 'link/messages.html', context)

@login_required
def archive_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if request.user.userprofile not in [message.sender, message.receiver]:
        messages.error(request, 'You do not have permission to archive this message.')
        return redirect('link:conversations')
    
    message.archive()
    messages.success(request, 'Message archived successfully.')
    return redirect('link:conversations')

@login_required
def unarchive_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if request.user.userprofile not in [message.sender, message.receiver]:
        messages.error(request, 'You do not have permission to unarchive this message.')
        return redirect('link:conversations')
    
    message.unarchive()
    messages.success(request, 'Message unarchived successfully.')
    return redirect('link:conversations')

@login_required
def filter_messages(request):
    message_type = request.GET.get('type')
    is_archived = request.GET.get('archived')
    
    # Get all unique conversations for the current user
    sent_messages = Message.objects.filter(sender=request.user.userprofile)
    received_messages = Message.objects.filter(receiver=request.user.userprofile)
    
    if message_type:
        sent_messages = sent_messages.filter(message_type=message_type)
        received_messages = received_messages.filter(message_type=message_type)
    
    if is_archived:
        sent_messages = sent_messages.filter(is_archived=True)
        received_messages = received_messages.filter(is_archived=True)
    else:
        sent_messages = sent_messages.filter(is_archived=False)
        received_messages = received_messages.filter(is_archived=False)
    
    # Combine and get unique user IDs
    user_ids = set()
    for msg in sent_messages.values('receiver').distinct():
        user_ids.add(msg['receiver'])
    for msg in received_messages.values('sender').distinct():
        user_ids.add(msg['sender'])
    
    # Get the conversations with the latest message
    conversations = []
    for user_id in user_ids:
        other_user = UserProfile.objects.get(id=user_id)
        last_message = Message.objects.filter(
            (Q(sender=request.user.userprofile) & Q(receiver=other_user)) |
            (Q(sender=other_user) & Q(receiver=request.user.userprofile))
        ).order_by('-created_at').first()
        
        unread_count = Message.objects.filter(
            sender=other_user,
            receiver=request.user.userprofile,
            is_read=False
        ).count()
        
        conversations.append({
            'other_user': other_user.user,
            'last_message': last_message,
            'unread_count': unread_count
        })
    
    context = {
        'conversations': conversations,
        'selected_type': message_type,
        'show_archived': is_archived == 'true'
    }
    return render(request, 'link/messages.html', context)

@login_required
def initiate_payment(request, order_id):
    """Initiate payment process"""
    order = get_object_or_404(Order, id=order_id)
    
    # Create payment transaction
    transaction = create_payment_transaction(order)
    
    # Initialize Paystack transaction
    paystack = PaystackAPI()
    callback_url = request.build_absolute_uri(
        reverse('link:payment_verify', args=[order.id])
    )
    
    response = paystack.initialize_transaction(
        email=order.buyer.user.email,
        amount=order.total_price,
        reference=transaction.reference,
        callback_url=callback_url
    )
    
    if response.get('status'):
        return JsonResponse({
            'status': True,
            'data': response['data']
        })
    return JsonResponse({
        'status': False,
        'message': 'Failed to initialize payment'
    })

def verify_payment(request, order_id):
    """Verify payment status"""
    order = get_object_or_404(Order, id=order_id)
    reference = request.GET.get('reference')
    
    if not reference:
        return redirect('link:payment_failed')
    
    try:
        transaction = PaymentTransaction.objects.get(reference=reference)
        paystack = PaystackAPI()
        response = paystack.verify_transaction(reference)
        
        if response.get('status') and response['data']['status'] == 'success':
            transaction.update_status('success')
            transaction.payment_data = response['data']
            transaction.save()
            return redirect('link:payment_success')
        
        transaction.update_status('failed')
        transaction.payment_data = response['data']
        transaction.save()
        return redirect('link:payment_failed')
        
    except PaymentTransaction.DoesNotExist:
        return redirect('link:payment_failed')

def payment_success(request):
    """Handle successful payment"""
    return render(request, 'link/payment_success.html')

def payment_failed(request):
    """Handle failed payment"""
    return render(request, 'link/payment_failed.html')

def payment_status(request, reference):
    """Check payment status"""
    try:
        transaction = PaymentTransaction.objects.get(reference=reference)
        return render(request, 'link/payment_status.html', {
            'transaction': transaction
        })
    except PaymentTransaction.DoesNotExist:
        return redirect('link:payment_failed')

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Check if user has already reviewed this product
    existing_review = Review.objects.filter(product=product, user=request.user.userprofile).first()
    if existing_review:
        messages.error(request, 'You have already reviewed this product.')
        return redirect('link:product_detail', slug=product.slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user.userprofile
            review.save()
            messages.success(request, 'Your review has been added successfully!')
            return redirect('link:product_detail', slug=product.slug)
    else:
        form = ReviewForm()
    
    return render(request, 'link/add_review.html', {
        'form': form,
        'product': product
    })

@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    
    # Check if user owns this review
    if review.user != request.user.userprofile:
        messages.error(request, 'You can only edit your own reviews.')
        return redirect('link:product_detail', slug=review.product.slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your review has been updated successfully!')
            return redirect('link:product_detail', slug=review.product.slug)
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'link/edit_review.html', {
        'form': form,
        'review': review
    })

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    
    # Check if user owns this review
    if review.user != request.user.userprofile:
        messages.error(request, 'You can only delete your own reviews.')
        return redirect('link:product_detail', slug=review.product.slug)
    
    if request.method == 'POST':
        product_slug = review.product.slug
        review.delete()
        messages.success(request, 'Your review has been deleted successfully!')
        return redirect('link:product_detail', slug=product_slug)
    
    return render(request, 'link/delete_review.html', {
        'review': review
    })
