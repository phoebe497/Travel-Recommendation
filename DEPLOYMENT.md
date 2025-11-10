# Deployment Guide

## Prerequisites

- Server with PHP 8.1 or higher
- MongoDB 4.0 or higher
- Composer installed
- Web server (Apache/Nginx)

## Production Deployment Steps

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install PHP 8.1 and extensions
sudo apt install -y php8.1 php8.1-cli php8.1-fpm php8.1-mongodb php8.1-mbstring php8.1-xml php8.1-curl

# Install Composer
curl -sS https://getcomposer.org/installer | php
sudo mv composer.phar /usr/local/bin/composer

# Install MongoDB (see MONGODB_SETUP.md)
```

### 2. Clone and Configure Application

```bash
# Clone repository
git clone https://github.com/phoebe497/Travel-Recommendation.git
cd Travel-Recommendation

# Install dependencies
composer install --optimize-autoloader --no-dev

# Set up environment
cp .env.example .env
php artisan key:generate

# Edit .env file
nano .env
```

### 3. Environment Configuration

Update `.env` for production:

```env
APP_ENV=production
APP_DEBUG=false
APP_URL=https://yourdomain.com

DB_CONNECTION=mongodb
DB_HOST=127.0.0.1
DB_PORT=27017
DB_DATABASE=travel_recommendation
DB_USERNAME=travel_app
DB_PASSWORD=your_secure_password

# Recommendation settings
RECOMMENDATION_OPTIMIZATION_ALGORITHM=greedy
RECOMMENDATION_CACHE_DURATION=120
```

### 4. Set Permissions

```bash
# Set proper ownership
sudo chown -R www-data:www-data /path/to/Travel-Recommendation

# Set directory permissions
sudo chmod -R 755 /path/to/Travel-Recommendation
sudo chmod -R 775 /path/to/Travel-Recommendation/storage
sudo chmod -R 775 /path/to/Travel-Recommendation/bootstrap/cache
```

### 5. Seed Database

```bash
php artisan db:seed
```

### 6. Configure Web Server

#### Nginx Configuration

Create `/etc/nginx/sites-available/travel-recommendation`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /path/to/Travel-Recommendation/public;

    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";

    index index.php;

    charset utf-8;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location = /favicon.ico { access_log off; log_not_found off; }
    location = /robots.txt  { access_log off; log_not_found off; }

    error_page 404 /index.php;

    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
        include fastcgi_params;
    }

    location ~ /\.(?!well-known).* {
        deny all;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/travel-recommendation /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Apache Configuration

Create `/etc/apache2/sites-available/travel-recommendation.conf`:

```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    DocumentRoot /path/to/Travel-Recommendation/public

    <Directory /path/to/Travel-Recommendation/public>
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/travel-recommendation-error.log
    CustomLog ${APACHE_LOG_DIR}/travel-recommendation-access.log combined
</VirtualHost>
```

Enable site:
```bash
sudo a2ensite travel-recommendation
sudo a2enmod rewrite
sudo systemctl reload apache2
```

### 7. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
```

### 8. Optimization

```bash
# Cache configuration
php artisan config:cache
php artisan route:cache

# Optimize Composer autoloader
composer dump-autoload --optimize
```

## Using Docker

### Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - .:/var/www/html
    environment:
      - DB_HOST=mongodb
      - DB_PORT=27017
      - DB_DATABASE=travel_recommendation
    depends_on:
      - mongodb

  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=travel_recommendation

volumes:
  mongodb_data:
```

Create `Dockerfile`:

```dockerfile
FROM php:8.1-fpm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libpng-dev \
    libonig-dev \
    libxml2-dev \
    zip \
    unzip

# Install PHP extensions
RUN pecl install mongodb \
    && docker-php-ext-enable mongodb \
    && docker-php-ext-install pdo mbstring exif pcntl bcmath gd

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Set working directory
WORKDIR /var/www/html

# Copy application
COPY . .

# Install dependencies
RUN composer install --optimize-autoloader --no-dev

# Set permissions
RUN chown -R www-data:www-data /var/www/html

CMD php artisan serve --host=0.0.0.0 --port=8000
```

Deploy with Docker:
```bash
docker-compose up -d
```

## Monitoring

### Application Logs

```bash
# View Laravel logs
tail -f storage/logs/laravel.log

# View MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# View web server logs
sudo tail -f /var/log/nginx/error.log
```

### Health Check

Create a health check endpoint (optional):

```php
// routes/web.php
Route::get('/health', function () {
    try {
        DB::connection()->getMongoDB()->command(['ping' => 1]);
        return response()->json(['status' => 'healthy'], 200);
    } catch (\Exception $e) {
        return response()->json(['status' => 'unhealthy', 'error' => $e->getMessage()], 503);
    }
});
```

## Backup Strategy

### Automated Backup Script

Create `/usr/local/bin/backup-travel-app.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/travel-recommendation"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup MongoDB
mongodump --db travel_recommendation --out $BACKUP_DIR/mongodb_$DATE

# Backup application files (optional)
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /path/to/Travel-Recommendation

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -mtime +7 -delete

echo "Backup completed: $DATE"
```

Make executable and add to cron:
```bash
chmod +x /usr/local/bin/backup-travel-app.sh

# Add to crontab (daily at 2 AM)
0 2 * * * /usr/local/bin/backup-travel-app.sh
```

## Scaling Considerations

### Load Balancing

Use Nginx as load balancer:

```nginx
upstream travel_backend {
    server app1.example.com;
    server app2.example.com;
    server app3.example.com;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://travel_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### MongoDB Replica Set

For high availability, configure MongoDB replica set (see MongoDB documentation).

### Caching

Add Redis for caching:

```env
CACHE_DRIVER=redis
REDIS_HOST=127.0.0.1
REDIS_PASSWORD=null
REDIS_PORT=6379
```

## Troubleshooting

### Common Issues

1. **500 Internal Server Error**
   - Check storage permissions
   - Review Laravel logs
   - Verify .env configuration

2. **MongoDB Connection Failed**
   - Verify MongoDB is running
   - Check credentials in .env
   - Review firewall rules

3. **Slow Recommendations**
   - Switch to greedy algorithm
   - Increase cache duration
   - Add database indexes

## Security Checklist

- [ ] Set `APP_DEBUG=false` in production
- [ ] Use strong database passwords
- [ ] Enable MongoDB authentication
- [ ] Configure firewall (UFW/iptables)
- [ ] Install SSL certificate
- [ ] Regular security updates
- [ ] Monitor application logs
- [ ] Implement rate limiting
- [ ] Regular backups
- [ ] Secure file permissions
