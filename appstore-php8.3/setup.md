# Setup Guide – appstore-php8.3 (Phase 1, MVP)

This document provides step-by-step instructions to install, configure, and run the vanilla PHP 8.3 storefront on an Oracle Linux 9 VM with Nginx and PHP-FPM. No APM or Logging Analytics is included.

---

## Prerequisites

Before you begin, ensure you have:

- Oracle Linux 9 x86_64 server with root access
- Internet access to install packages and Composer dependencies
- Firewall access on TCP port 80 for HTTP

---

## Installation Steps

### 1. Update System

```bash
sudo dnf -y update
```

### 2. Install PHP 8.3, Nginx, and Dependencies

Oracle Linux 9 may not provide PHP 8.3 in the default AppStream. Choose one of the following options:

#### Option A – Use Remi's PHP 8.3 (Recommended)

```bash
sudo dnf -y install https://rpms.remirepo.net/enterprise/remi-release-9.rpm
sudo dnf -y module reset php
sudo dnf -y module enable php:remi-8.3
sudo dnf -y install nginx php php-fpm php-pdo php-sqlite3 php-mbstring php-json unzip git
```

#### Option B – Use Distribution PHP (if 8.3 already available)

```bash
sudo dnf -y install nginx php php-fpm php-pdo php-sqlite3 php-mbstring php-json unzip git
```

### 3. Install Composer

Check if Composer exists:

```bash
composer --version
```

If not installed, use the official installer:

```bash
php -r "copy('https://getcomposer.org/installer', 'composer-setup.php');"
php composer-setup.php --install-dir=/usr/local/bin --filename=composer
php -r "unlink('composer-setup.php');"
composer --version
```

### 4. Obtain the Application Source

If you already have this code in your home repository, copy it to `/var/www`. Otherwise, clone a repository or transfer files.

Assuming the code is present under `/home/opc/github/devspace/appstore-php8.3`:

```bash
sudo mkdir -p /var/www
sudo rsync -a /home/opc/github/devspace/appstore-php8.3/ /var/www/appstore-php8.3/
```

### 5. Install PHP Dependencies

```bash
cd /var/www/appstore-php8.3
composer install --no-interaction --no-dev --prefer-dist
```

This will create the `vendor/` directory and autoload files.

### 6. Initialize Directories and Permissions

Create writable directories for the app and set ownership to nginx:

```bash
sudo chown -R nginx:nginx /var/www/appstore-php8.3
sudo find /var/www/appstore-php8.3 -type d -exec chmod 755 {} \;
sudo find /var/www/appstore-php8.3 -type f -exec chmod 644 {} \;
```

Ensure database and logs directories are writable by PHP-FPM:

```bash
sudo mkdir -p /var/www/appstore-php8.3/database /var/www/appstore-php8.3/logs
sudo chown -R nginx:nginx /var/www/appstore-php8.3/database /var/www/appstore-php8.3/logs
sudo chmod 775 /var/www/appstore-php8.3/database /var/www/appstore-php8.3/logs

# Ensure application log file exists with correct ownership and permissions
sudo touch /var/www/appstore-php8.3/logs/app.log
sudo chown nginx:nginx /var/www/appstore-php8.3/logs/app.log
sudo chmod 664 /var/www/appstore-php8.3/logs/app.log
```

#### SELinux Configuration

If SELinux is enforcing, either set correct contexts or temporarily test with permissive mode. Recommended contexts:

```bash
sudo chcon -R -t httpd_sys_rw_content_t /var/www/appstore-php8.3/database
sudo chcon -R -t httpd_sys_rw_content_t /var/www/appstore-php8.3/logs
```

### 7. Initialize SQLite Database

Run the init script to create tables and seed user and products. This creates `database/appstore.db`:

```bash
cd /var/www/appstore-php8.3
php scripts/init_db.php
```

After running, re-apply ownership to ensure Nginx/PHP-FPM can write to the database:

```bash
sudo chown -R nginx:nginx /var/www/appstore-php8.3/database
```

### 8. Nginx Configuration

Create a server block at `/etc/nginx/conf.d/appstore.conf`:

```bash
sudo tee /etc/nginx/conf.d/appstore.conf > /dev/null <<'NGINX'
server {
    listen 80;
    server_name _;
    root /var/www/appstore-php8.3/public;
    index index.php;

    access_log /var/www/appstore-php8.3/logs/access.log;
    error_log  /var/www/appstore-php8.3/logs/nginx_error.log;

    location / {
        try_files $uri /index.php$is_args$args;
    }

    location ~ \.php$ {
        include fastcgi_params;
        fastcgi_pass unix:/run/php-fpm/appstore.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_buffer_size 32k;
        fastcgi_buffers 4 32k;
    }

    location ~* \.(jpg|jpeg|png|gif|css|js|ico|woff|woff2)$ {
        expires 30d;
        access_log off;
    }
}
NGINX
```

### 9. PHP-FPM Pool Configuration

Create a dedicated pool (optional but recommended) at `/etc/php-fpm.d/appstore.conf`:

```bash
sudo tee /etc/php-fpm.d/appstore.conf > /dev/null <<'POOL'
[appstore]
user = nginx
group = nginx
listen = /run/php-fpm/appstore.sock
listen.owner = nginx
listen.group = nginx
pm = dynamic
pm.max_children = 10
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 3
php_admin_value[error_log] = /var/www/appstore-php8.3/logs/php_error.log
php_admin_flag[log_errors] = on
POOL
```

> **Note:** If you already have a default pool (`/etc/php-fpm.d/www.conf`), ensure it's compatible or disable it if you want to use only the appstore pool. The listen socket path above matches the Nginx config.

### 10. Enable and Restart Services

```bash
sudo systemctl enable php-fpm
sudo systemctl enable nginx
sudo systemctl restart php-fpm
sudo systemctl restart nginx
```

### 11. Open Firewall

If firewalld is active:

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
```

#### Network Security Note

- In this lab, ingress is restricted at the network/security list to your workstation's IP (CIDR /32) for any port. This ensures only your test computer/laptop can reach the VM.
- Egress is allowed to 0.0.0.0/0 for outbound connectivity (e.g., package installs, updates).
- With `server_name _` and this ingress rule, only requests originating from your /32 can access the site even though Nginx listens on :80.
- For production, consider limiting exposed ports and hardening security groups, and disable simulation endpoints if not required.

### 12. Validate the Application

Navigate to `http://<VM_IP>/` in your browser. You should see the login page at `/login` or be redirected there.

#### Default Credentials

- **Username:** `admin`
- **Password:** `demo123`

#### Available Features

- Browse products at `/products`
- View product details at `/product/{id}`
- Add items to cart
- Update quantities and remove items
- Checkout at `/checkout`
- View order history at `/orders`

#### Simulation Endpoints

- `http://<VM_IP>/simulate/slow` - Responds after 3-5 seconds
- `http://<VM_IP>/simulate/error` - HTTP 500 generated intentionally

---

## Troubleshooting

### Log Files

- **Application log:** `/var/www/appstore-php8.3/logs/app.log`
- **Nginx access log:** `/var/www/appstore-php8.3/logs/access.log`
- **Nginx error log:** `/var/www/appstore-php8.3/logs/nginx_error.log`
- **PHP-FPM error log:** `/var/www/appstore-php8.3/logs/php_error.log`

### Common Issues

**403/500 errors due to SELinux contexts:**

```bash
sudo chcon -R -t httpd_sys_rw_content_t /var/www/appstore-php8.3/database
sudo chcon -R -t httpd_sys_rw_content_t /var/www/appstore-php8.3/logs
```

**Missing vendor/autoload.php:**

```bash
cd /var/www/appstore-php8.3
composer install
```

**Database permission errors:**

```bash
sudo chown -R nginx:nginx /var/www/appstore-php8.3/database
```

---

## Local Development (Optional)

If you want to run locally without Nginx:

```bash
cd /var/www/appstore-php8.3
composer install
php scripts/init_db.php
composer start
```

Browse to `http://localhost:8080`

---

## Security Hardening (Optional)

### Server Configuration

Keep wildcard `server_name _` if you rely on upstream security lists/NSGs restricting ingress to your /32. Otherwise, set an explicit FQDN/IP and adjust DNS/firewall accordingly.

### Nginx Security Headers

Add inside your server block (alternative to app-level headers already set in the app):

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

### Hide Nginx Version

In `/etc/nginx/nginx.conf` under `http { ... }` add:

```nginx
server_tokens off;
```

### Rate Limiting

Consider `limit_req_zone`/`limit_req` for POST `/login` to mitigate brute force attempts.

### HTTPS/TLS

Terminate TLS at Nginx or an upstream load balancer. When behind TLS (or with `HTTP_X_FORWARDED_PROTO=https`), the app sets secure session cookies automatically.

### Production Best Practices

- Disable simulation endpoints (`/simulate/*`)
- Consider CSRF protection for POST forms
- Implement stricter Content-Security-Policy

---

## Summary

This completes the Phase 1 setup. The application is now ready for use and future instrumentation phases.
