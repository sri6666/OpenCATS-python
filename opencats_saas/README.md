# OpenCATS SaaS - Multi-Tenant Applicant Tracking System

Production-ready Flask application for running OpenCATS as a Software-as-a-Service platform on AWS/GCP.

## 🚀 Features

### Core ATS Features
- **Candidate Management** - Full CRUD with resume parsing, duplicate detection
- **Job Orders** - Job posting management with pipeline tracking
- **Companies & Contacts** - Client relationship management
- **Pipeline** - Visual candidate-to-job workflow
- **Activities** - Call, email, meeting logging
- **Search** - Full-text search across all entities
- **Reports** - Dashboard statistics and analytics

### SaaS Features
- **Multi-Tenancy** - Complete data isolation per customer
- **Subscription Plans** - Starter ($49), Professional ($99), Enterprise ($249)
- **Usage Limits** - Automatic enforcement based on plan
- **Stripe Integration** - Payment processing ready
- **14-Day Free Trial** - Automatic trial management
- **Subdomain Routing** - customer.yourdomain.com
- **Custom Domains** - Bring your own domain (Enterprise)

### Technical Features
- **Cloud-Ready** - Deploy to AWS/GCP with Docker
- **File Storage** - Local or AWS S3
- **Background Jobs** - Celery task queue
- **Email** - AWS SES or SMTP
- **Caching** - Redis-backed
- **Rate Limiting** - Protection against abuse
- **Error Tracking** - Sentry integration
- **Security** - bcrypt passwords, CSRF protection, SQL injection prevention

## 📋 Requirements

- Python 3.9+
- MySQL 8.0+ or MariaDB 10.6+
- Redis 6.0+
- (Optional) Elasticsearch 8.x for advanced search
- (Optional) AWS account for S3 storage

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/opencats-saas.git
cd opencats-saas
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Initialize Database
```bash
# Create database
mysql -u root -p -e "CREATE DATABASE opencats_saas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Run migrations
flask db upgrade

# Seed initial data
flask seed-db
```

### 6. Run Application
```bash
# Development
python run.py

# Or with Flask CLI
flask run

# Production (with Gunicorn)
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t opencats-saas .
```

### Run with Docker Compose
```bash
docker-compose up -d
```

### Deploy to AWS ECS/Fargate
```bash
# See deploy/aws/ directory for CloudFormation templates
```

### Deploy to Google Cloud Run
```bash
gcloud run deploy opencats-saas \
  --image gcr.io/PROJECT_ID/opencats-saas \
  --platform managed \
  --region us-central1
```

## 📁 Project Structure

```
opencats_saas/
├── app/
│   ├── __init__.py           # Application factory
│   ├── extensions.py         # Flask extensions
│   ├── models.py             # Database models
│   │
│   ├── auth/                 # Authentication
│   │   ├── views.py
│   │   └── forms.py
│   │
│   ├── candidates/           # Candidates module
│   │   ├── views.py
│   │   └── forms.py
│   │
│   ├── joborders/            # Job orders module
│   ├── companies/            # Companies module
│   ├── contacts/             # Contacts module
│   ├── api/                  # REST API
│   ├── main/                 # Main/dashboard
│   ├── admin/                # Admin panel
│   │
│   ├── templates/            # Jinja2 templates
│   ├── static/               # CSS, JS, images
│   │
│   └── utils/                # Utilities
│       ├── decorators.py
│       ├── permissions.py
│       ├── file_handler.py
│       └── resume_parser.py
│
├── migrations/               # Alembic migrations
├── tests/                    # Test suite
├── config.py                 # Configuration
├── run.py                    # Entry point
└── requirements.txt          # Dependencies
```

## 🔧 Configuration

### Subscription Plans

Edit in `config.py`:

```python
SUBSCRIPTION_PLANS = {
    'starter': {
        'name': 'Starter',
        'price': 49,
        'features': {
            'max_users': 3,
            'max_candidates': 500,
            'max_jobs': 20,
            'storage_gb': 5,
        }
    },
    # ... more plans
}
```

### Email Templates

Customize email templates in `app/templates/email/`:
- `welcome.html` - Welcome email for new signups
- `trial_ending.html` - Trial expiration warning
- `invoice.html` - Payment receipts

### Custom Branding

- Logo: `app/static/img/logo.png`
- Favicon: `app/static/img/favicon.ico`
- Colors: `app/static/css/custom.css`

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/unit/test_candidates.py
```

## 📊 Monitoring

### Application Metrics
- Sentry for error tracking
- Prometheus metrics endpoint: `/metrics`
- Health check: `/health`

### Database Performance
```sql
-- Check slow queries
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;
```

## 🔐 Security

### Best Practices Implemented
✅ bcrypt password hashing (upgraded from MD5)
✅ CSRF protection on all forms
✅ SQL injection prevention (SQLAlchemy ORM)
✅ XSS protection (Jinja2 auto-escaping)
✅ Rate limiting on auth endpoints
✅ Secure session cookies (HTTPOnly, Secure, SameSite)
✅ File upload validation
✅ Multi-tenant data isolation

### Security Checklist
- [ ] Change SECRET_KEY in production
- [ ] Enable HTTPS (SSL_ENABLED=true)
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Review user access levels
- [ ] Enable Sentry error tracking
- [ ] Configure rate limiting
- [ ] Set up log monitoring

## 💰 Pricing & Billing

### Integration with Stripe

1. Create products in Stripe Dashboard
2. Add product IDs to `config.py`
3. Set webhook endpoint: `https://yourdomain.com/webhooks/stripe`
4. Handle subscription events in `app/billing/webhooks.py`

### Webhook Events
- `customer.subscription.created` - New subscription
- `customer.subscription.updated` - Plan change
- `customer.subscription.deleted` - Cancellation
- `invoice.payment_succeeded` - Successful payment
- `invoice.payment_failed` - Failed payment

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] Set FLASK_ENV=production
- [ ] Configure production database
- [ ] Set up Redis instance
- [ ] Configure S3 bucket
- [ ] Set up email service (SES)
- [ ] Create Stripe products
- [ ] Set up monitoring (Sentry)
- [ ] Configure SSL certificate
- [ ] Set up CDN (CloudFront/CloudFlare)
- [ ] Create backup strategy

### Launch
- [ ] Run database migrations
- [ ] Seed initial data
- [ ] Test payment flow
- [ ] Test email sending
- [ ] Load test application
- [ ] Security audit
- [ ] Set up status page
- [ ] Prepare support documentation

## 📝 API Documentation

REST API available at `/api/v1/`

### Authentication
```bash
# Get token
curl -X POST https://api.yourdomain.com/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Use token
curl https://api.yourdomain.com/api/v1/candidates \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Endpoints
- `GET /api/v1/candidates` - List candidates
- `POST /api/v1/candidates` - Create candidate
- `GET /api/v1/candidates/{id}` - Get candidate
- `PUT /api/v1/candidates/{id}` - Update candidate
- `DELETE /api/v1/candidates/{id}` - Delete candidate

Full API docs: https://yourdomain.com/api/docs

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 💬 Support

- Documentation: https://docs.yourdomain.com
- Email: support@yourdomain.com
- Community: https://community.yourdomain.com
- Issues: https://github.com/yourusername/opencats-saas/issues

## 🗺️ Roadmap

### Q1 2024
- [ ] Mobile app (iOS/Android)
- [ ] Advanced analytics dashboard
- [ ] AI-powered resume matching
- [ ] Integrations (LinkedIn, Indeed, ZipRecruiter)

### Q2 2024
- [ ] Video interview scheduling
- [ ] Automated email campaigns
- [ ] Custom workflows
- [ ] White-label options

### Q3 2024
- [ ] Advanced reporting
- [ ] Compliance tools (GDPR, CCPA)
- [ ] Multi-language support
- [ ] Enterprise SSO (SAML, OAuth)

---

**Built with ❤️ using Flask, SQLAlchemy, and modern Python**
