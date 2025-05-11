import json
import hmac
import hashlib
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import PaymentTransaction

@csrf_exempt
@require_POST
def paystack_webhook(request):
    """Handle Paystack webhook events"""
    # Get the Paystack signature from the request header
    paystack_signature = request.headers.get('x-paystack-signature')
    
    if not paystack_signature:
        return HttpResponse(status=400)
    
    # Verify the signature
    computed_hmac = hmac.new(
        settings.PAYSTACK_WEBHOOK_SECRET.encode('utf-8'),
        request.body,
        hashlib.sha512
    ).hexdigest()
    
    if not hmac.compare_digest(computed_hmac, paystack_signature):
        return HttpResponse(status=400)
    
    # Parse the webhook payload
    payload = json.loads(request.body)
    event = payload.get('event')
    data = payload.get('data')
    
    if not event or not data:
        return HttpResponse(status=400)
    
    # Handle different event types
    if event == 'charge.success':
        reference = data.get('reference')
        try:
            transaction = PaymentTransaction.objects.get(reference=reference)
            transaction.update_status('success')
            transaction.payment_data = data
            transaction.save()
        except PaymentTransaction.DoesNotExist:
            return HttpResponse(status=404)
    
    elif event == 'charge.failed':
        reference = data.get('reference')
        try:
            transaction = PaymentTransaction.objects.get(reference=reference)
            transaction.update_status('failed')
            transaction.payment_data = data
            transaction.save()
        except PaymentTransaction.DoesNotExist:
            return HttpResponse(status=404)
    
    elif event == 'transfer.success':
        # Handle successful bank transfers
        reference = data.get('reference')
        try:
            transaction = PaymentTransaction.objects.get(reference=reference)
            transaction.update_status('success')
            transaction.payment_data = data
            transaction.save()
        except PaymentTransaction.DoesNotExist:
            return HttpResponse(status=404)
    
    return HttpResponse(status=200) 