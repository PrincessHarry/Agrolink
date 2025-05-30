# Agrolink - Agricultural Marketplace Platform

Agrolink is a comprehensive agricultural marketplace platform that connects farmers, buyers, and agricultural service providers. The platform facilitates the buying and selling of agricultural products, provides real-time communication, and handles secure payments through Paystack integration.

## Features

- **User Management**
  - User registration and authentication
  - Profile management for farmers and buyers
  - Role-based access control

- **Product Management**
  - Product listing and categorization
  - Image upload and management
  - Product search and filtering
  - Inventory tracking

- **Order System**
  - Shopping cart functionality
  - Order processing and tracking
  - Order history and status updates
  - Real-time order notifications

- **Payment Integration**
  - Secure payment processing via Paystack
  - Multiple payment methods support
  - Payment status tracking
  - Transaction history

- **Communication**
  - Real-time chat between users
  - Messaging system
  - Order notifications
  - Email notifications

- **Admin Dashboard**
  - User management
  - Product moderation
  - Order management
  - Transaction monitoring

## Technology Stack

- **Backend**: Django 5.2
- **Frontend**: HTML, CSS (Tailwind CSS), JavaScript
- **Database**: SQLite (Development), PostgreSQL (Production)
- **Real-time Features**: Django Channels with Redis
- **Payment Gateway**: Paystack
- **Email Service**: Gmail SMTP

## Prerequisites

- Python 3.8+
- Redis Server
- Git
- Virtual Environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/agrolink.git
cd agrolink
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following variables:
```env
# Django Settings
DEBUG=True
SECRET_KEY=your-django-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Paystack Settings
PAYSTACK_SECRET_KEY=your_paystack_secret_key
PAYSTACK_PUBLIC_KEY=your_paystack_public_key
PAYSTACK_WEBHOOK_SECRET=your_paystack_webhook_secret
PAYSTACK_CURRENCY=NGN

# Email Settings (Gmail)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_gmail@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
```

5. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Start the development server:
```bash
python manage.py runserver
```

## Running with Redis (for real-time features)

1. Install Redis on your system
2. Start Redis server:
```bash
redis-server
```

3. Run the development server with Daphne:
```bash
daphne Agrolink.asgi:application
```



## API Endpoints

- `/api/products/` - Product listing and management
- `/api/orders/` - Order processing
- `/api/payments/` - Payment processing
- `/api/messages/` - Messaging system
- `/api/users/` - User management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request



## Acknowledgments

- Django Documentation
- Paystack API Documentation
- Tailwind CSS
- Django Channels

