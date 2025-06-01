from django.test import TestCase, Client
from django.urls import reverse
from .models import UserProfile, Product, Order
from django.contrib.auth.models import User
from decimal import Decimal

# Create your tests here.

class PaymentTest(TestCase):
    def setUp(self):
        # Create test users
        self.buyer = User.objects.create_user(
            username='testbuyer',
            email='testbuyer@example.com',
            password='testpass123'
        )
        self.seller = User.objects.create_user(
            username='testseller',
            email='testseller@example.com',
            password='testpass123'
        )
        
        # Create user profiles
        self.buyer_profile = UserProfile.objects.create(
            user=self.buyer,
            user_type='buyer',
            phone_number='1234567890',
            address='Test Address'
        )
        self.seller_profile = UserProfile.objects.create(
            user=self.seller,
            user_type='farmer',
            phone_number='0987654321',
            address='Test Address'
        )
        
        # Create test product
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('1000.00'),
            quantity=10,
            seller=self.seller_profile,
            category='vegetables',
            status='available'
        )
        
        # Create test order
        self.order = Order.objects.create(
            buyer=self.buyer_profile,
            total_price=Decimal('1000.00'),
            shipping_address='Test Address'
        )
        
        self.client = Client()
        self.client.login(username='testbuyer', password='testpass123')

    def test_payment_initialization(self):
        """Test payment initialization"""
        response = self.client.post(
            reverse('link:initiate_payment', args=[self.order.id])
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('data', data)
        
    def test_payment_verification(self):
        """Test payment verification"""
        # First initialize payment
        init_response = self.client.post(
            reverse('link:initiate_payment', args=[self.order.id])
        )
        data = init_response.json()
        
        # Test verification with reference
        verify_url = reverse('link:payment_verify', args=[self.order.id])
        response = self.client.get(f"{verify_url}?reference={data['data']['reference']}")
        self.assertEqual(response.status_code, 302)  # Should redirect
