# OpenCATS SaaS - Local Setup Guide

## Quick Start (5 minutes)

### Prerequisites
- Python 3.11+
- MySQL 8.0 (or use Docker)
- Redis (optional, can disable for local testing)

### Option 1: Automated Setup (Recommended)

```bash
# Run the setup script
chmod +x setup_local.sh
./setup_local.sh
```

### Option 2: Manual Setup

#### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Setup Local Database (MySQL)

**Using Docker (easiest):**
```bash
docker run --name opencats-mysql \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=opencats_dev \
  -e MYSQL_USER=opencats \
  -e MYSQL_PASSWORD=opencats123 \
  -p 3306:3306 \
  -d mysql:8.0
```

**Or install MySQL locally:**
```bash
# Ubuntu/Debian
sudo apt-get install mysql-server

# macOS
brew install mysql

# Create database
mysql -u root -p
CREATE DATABASE opencats_dev;
CREATE USER 'opencats'@'localhost' IDENTIFIED BY 'opencats123';
GRANT ALL PRIVILEGES ON opencats_dev.* TO 'opencats'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 4. Setup Redis (Optional)

**Using Docker:**
```bash
docker run --name opencats-redis -p 6379:6379 -d redis:alpine
```

**Or install locally:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis
redis-server
```

#### 5. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with local values
nano .env  # or your favorite editor
```

**Minimal .env for local testing:**
```env
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production

# Database
DATABASE_URL=mysql+pymysql://opencats:opencats123@localhost/opencats_dev

# Redis (optional - comment out if not using)
REDIS_URL=redis://localhost:6379/0

# Stripe (optional for local testing)
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here

# Email (optional)
MAIL_SERVER=localhost
MAIL_PORT=1025
```

#### 6. Initialize Database

```bash
# Set Flask app
export FLASK_APP=run.py

# Initialize database
flask init_db

# Seed with demo data
flask seed_db
```

#### 7. Run the Application

```bash
# Development server
python run.py

# Or with Flask CLI
flask run --debug
```

#### 8. Access the Application

Open your browser to:
- **Application:** http://localhost:5000
- **Login:** admin / admin123 (from seed_db)

## Testing Features

### 1. Sign Up Flow

Visit http://localhost:5000/auth/signup and create a new tenant:
- Company Name: Test Company
- Subdomain: testcompany
- Email: test@example.com
- Password: Test123!

### 2. Dashboard

After login, you'll see:
- Statistics cards
- Quick actions
- Recent candidates/jobs
- Hot candidates

### 3. Add a Candidate

1. Go to Candidates → Add Candidate
2. Fill in details
3. Upload a resume (PDF or DOCX)
4. See auto-extracted skills

### 4. Create a Job Order

1. Go to Job Orders → Add Job
2. Create a new position
3. Go to Pipeline view
4. Drag candidates between stages

### 5. Test REST API

```bash
# Login to get JWT token
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Use token to list candidates
curl http://localhost:5000/api/v1/candidates \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Troubleshooting

### Database Connection Error

**Error:** `Can't connect to MySQL server`

**Solution:**
```bash
# Check MySQL is running
docker ps | grep mysql  # If using Docker
# or
sudo systemctl status mysql  # If installed locally

# Verify credentials in .env match your MySQL setup
```

### Import Errors

**Error:** `ModuleNotFoundError`

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install specific missing package
pip install flask-sqlalchemy flask-login
```

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Use different port
flask run --port 5001

# Or kill process on port 5000
lsof -ti:5000 | xargs kill -9  # macOS/Linux
```

### Redis Connection Error (Optional)

If you see Redis errors but don't need it for basic testing:

**Solution:**
```bash
# Comment out Redis in .env
# REDIS_URL=redis://localhost:6379/0

# Redis is only needed for:
# - Session storage (falls back to cookies)
# - Celery tasks (won't affect basic features)
```

## Development Tips

### Hot Reload

The dev server auto-reloads on code changes:
```bash
flask run --debug
```

### Database Migrations

After changing models:
```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

### Reset Database

```bash
# Drop and recreate
flask db downgrade base
flask db upgrade
flask seed_db
```

### View Routes

```bash
flask routes
```

### Flask Shell

```bash
flask shell

# Now you can interact with models
>>> from app.models import User, Candidate
>>> User.query.all()
>>> Candidate.query.count()
```

## Testing Different Plans

The seed command creates a site with 'starter' plan. To test limits:

```python
# In Flask shell
from app.models import Site
from app.extensions import db

site = Site.query.first()

# Change to professional
site.subscription_plan = 'professional'
db.session.commit()

# Check limits
site.can_add_candidate()
```

## Performance Testing

```bash
# Install load testing tool
pip install locust

# Run load test
locust -f tests/locustfile.py
```

## Docker Local Testing

If you prefer Docker for everything:

```bash
# Use docker-compose
docker-compose up -d db redis

# Run Flask locally but use Docker services
export DATABASE_URL=mysql+pymysql://opencats:password@localhost/opencats_saas
export REDIS_URL=redis://localhost:6379/0
python run.py
```

## Next Steps

Once running locally:
1. ✅ Test signup and login
2. ✅ Create candidates and upload resumes
3. ✅ Create job orders
4. ✅ Test pipeline drag-and-drop
5. ✅ Try REST API endpoints
6. ✅ Test search functionality
7. ✅ Check admin dashboard

## Need Help?

Check the logs:
```bash
# Flask outputs to console in debug mode
# Check for error messages

# Database logs
docker logs opencats-mysql  # If using Docker
```

## Stopping Services

```bash
# Stop Flask
Ctrl+C in terminal

# Stop Docker services
docker stop opencats-mysql opencats-redis
```

## Clean Up

```bash
# Remove Docker containers
docker rm opencats-mysql opencats-redis

# Remove virtual environment
deactivate
rm -rf venv/

# Drop database
mysql -u root -p
DROP DATABASE opencats_dev;
```
