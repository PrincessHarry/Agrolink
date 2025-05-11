import requests
from django.conf import settings
from django.urls import reverse
from .models import PaymentTransaction, Order
import time

class PaystackAPI:
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.public_key = settings.PAYSTACK_PUBLIC_KEY
        self.base_url = "https://api.paystack.co"
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def initialize_transaction(self, email, amount, reference, callback_url):
        """Initialize a new transaction"""
        url = f"{self.base_url}/transaction/initialize"
        data = {
            "email": email,
            "amount": int(amount * 100),  # Convert to kobo
            "reference": reference,
            "callback_url": callback_url,
            "currency": settings.PAYSTACK_CURRENCY,
            "channels": ["card", "bank", "ussd", "qr", "mobile_money", "bank_transfer"]
        }
        
        response = requests.post(url, json=data, headers=self.headers)
        return response.json()

    def verify_transaction(self, reference):
        """Verify a transaction"""
        url = f"{self.base_url}/transaction/verify/{reference}"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def create_transfer_recipient(self, name, account_number, bank_code):
        """Create a transfer recipient for bank transfers"""
        url = f"{self.base_url}/transferrecipient"
        data = {
            "type": "nuban",
            "name": name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": settings.PAYSTACK_CURRENCY
        }
        
        response = requests.post(url, json=data, headers=self.headers)
        return response.json()

    def initiate_transfer(self, recipient_code, amount, reference):
        """Initiate a bank transfer"""
        url = f"{self.base_url}/transfer"
        data = {
            "source": "balance",
            "recipient": recipient_code,
            "amount": int(amount * 100),  # Convert to kobo
            "reference": reference
        }
        
        response = requests.post(url, json=data, headers=self.headers)
        return response.json()

def create_payment_transaction(order):
    """Create a new payment transaction"""
    transaction = PaymentTransaction.objects.create(
        order=order,
        reference=f"PAY-{order.id}-{int(time.time())}",
        amount=order.total_price,
        payment_method='card'  # Default to card, will be updated based on actual payment method
    )
    return transaction

def get_transaction_status(self, reference):
    """Get transaction status from Paystack"""
    response = requests.get(
        f'{self.base_url}/transaction/{reference}',
        headers=self.headers
    )

    if response.status_code == 200:
        return response.json()
    return None 