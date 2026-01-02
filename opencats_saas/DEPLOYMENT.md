# OpenCATS SaaS - Deployment Guide

## Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- Domain name with DNS configured
- At least 2GB RAM, 20GB disk space
- SSL certificate (Let's Encrypt recommended)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd opencats_saas
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` and set:

```bash
# Required
SECRET_KEY=<generate-with: python -c 'import secrets; print(secrets.token_hex(32))'>
MYSQL_ROOT_PASSWORD=<strong-password>
MYSQL_PASSWORD=<strong-password>

# Optional but recommended
STRIPE_SECRET_KEY=sk_live_...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
SENTRY_DSN=https://...@sentry.io/...
```

### 3. Update Nginx Configuration

Edit `nginx/conf.d/opencats.conf` and replace `yourdomain.com` with your actual domain.

### 4. Start Services

```bash
# Build and start all services
docker-compose up -d

# Initialize database
docker-compose exec web flask init_db

# Create admin user
docker-compose exec web flask seed_db
```

### 5. Setup SSL (Let's Encrypt)

```bash
# Initial certificate
docker-compose run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email

# Reload nginx
docker-compose exec nginx nginx -s reload
```

### 6. Verify Deployment

```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs web
docker-compose logs celery-worker

# Test application
curl https://yourdomain.com/health
```

## Service Management

### Start/Stop Services

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart web
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery-worker
docker-compose logs -f db
```

### Database Management

```bash
# Access MySQL shell
docker-compose exec db mysql -u opencats -p opencats_saas

# Create database backup
docker-compose exec db mysqldump -u opencats -p opencats_saas > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T db mysql -u opencats -p opencats_saas < backup.sql

# Run migrations
docker-compose exec web flask db upgrade
```

### Scaling

```bash
# Scale web workers
docker-compose up -d --scale web=3

# Scale Celery workers
docker-compose up -d --scale celery-worker=2
```

## Production Checklist

### Security

- [ ] Set strong `SECRET_KEY`
- [ ] Change default database passwords
- [ ] Enable SSL/HTTPS
- [ ] Configure firewall (allow only 80, 443)
- [ ] Set up fail2ban for brute force protection
- [ ] Enable Sentry for error tracking
- [ ] Disable debug mode (`FLASK_ENV=production`)
- [ ] Review and restrict CORS settings

### Performance

- [ ] Configure Redis persistence
- [ ] Set up database indexes
- [ ] Enable gzip compression in nginx
- [ ] Configure CDN for static files (optional)
- [ ] Set up database read replicas (optional)
- [ ] Configure connection pooling

### Monitoring

- [ ] Set up application monitoring (Sentry)
- [ ] Configure server monitoring (Uptime Robot, Pingdom)
- [ ] Set up log aggregation (ELK, Datadog)
- [ ] Configure alerts for critical errors
- [ ] Monitor disk usage
- [ ] Monitor database performance

### Backup

- [ ] Automated database backups (daily)
- [ ] Backup uploads directory
- [ ] Test backup restoration
- [ ] Off-site backup storage
- [ ] Backup retention policy

## Common Tasks

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build web
docker-compose up -d web

# Run database migrations
docker-compose exec web flask db upgrade
```

### Clear Cache

```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

### View Application Logs

```bash
# Real-time logs
docker-compose logs -f web

# Last 100 lines
docker-compose logs --tail=100 web
```

### Shell Access

```bash
# Flask shell
docker-compose exec web flask shell

# Container bash shell
docker-compose exec web bash
```

## Troubleshooting

### Application won't start

```bash
# Check logs
docker-compose logs web

# Common issues:
# - Database connection failed: Check MYSQL_PASSWORD
# - Redis connection failed: Ensure redis service is running
# - Port already in use: Change port mapping in docker-compose.yml
```

### Database connection errors

```bash
# Verify database is running
docker-compose ps db

# Test database connection
docker-compose exec web python -c "from app import create_app; app = create_app(); print('OK')"

# Check database credentials in .env
```

### Nginx 502 Bad Gateway

```bash
# Ensure web service is running
docker-compose ps web

# Check web service logs
docker-compose logs web

# Verify upstream configuration
docker-compose exec nginx nginx -t
```

### Celery tasks not processing

```bash
# Check Celery worker status
docker-compose logs celery-worker

# Check Redis connection
docker-compose exec celery-worker python -c "from app.extensions import celery_app; print(celery_app.control.inspect().active())"

# Restart Celery workers
docker-compose restart celery-worker
```

## Performance Tuning

### Gunicorn Workers

Edit `docker-compose.yml`:

```yaml
# Formula: (2 x CPU cores) + 1
command: gunicorn --bind 0.0.0.0:5000 --workers 5 --threads 2 run:app
```

### Database Connection Pool

Edit `config.py`:

```python
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_MAX_OVERFLOW = 20
SQLALCHEMY_POOL_TIMEOUT = 30
SQLALCHEMY_POOL_RECYCLE = 3600
```

### Redis Memory Limit

Edit `docker-compose.yml`:

```yaml
redis:
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

## AWS Deployment

### Using AWS ECS

1. Push Docker image to ECR
2. Create ECS task definition
3. Set up Application Load Balancer
4. Configure RDS for MySQL
5. Use ElastiCache for Redis
6. Set up CloudWatch for monitoring

### Using AWS EC2

1. Launch EC2 instance (t3.medium or larger)
2. Install Docker and Docker Compose
3. Follow standard deployment steps
4. Use RDS for production database
5. Configure S3 for file storage

## GCP Deployment

### Using Cloud Run

1. Build and push to Container Registry
2. Deploy to Cloud Run
3. Configure Cloud SQL for MySQL
4. Use Memorystore for Redis
5. Set up Cloud Storage for uploads

## Monitoring URLs

- **Application:** https://yourdomain.com
- **Admin:** https://yourdomain.com/admin
- **API:** https://yourdomain.com/api/v1
- **Health Check:** https://yourdomain.com/health

## Support

For issues or questions:
- GitHub Issues: <repository-url>/issues
- Email: support@yourdomain.com
- Documentation: <docs-url>
