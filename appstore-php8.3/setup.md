# Setup Guide — appstore-php8.3 (Phase 1, MVP)

This document provides step-by-step instructions to install, configure, and run the vanilla PHP 8.3 storefront on an Oracle Linux 9 VM with Nginx and PHP-FPM. No APM or Logging Analytics is included.

Prerequisites
- Oracle Linux 9 x86_64 server with root access
- Internet access to install packages and Composer dependencies
- Firewall access on TCP 80 for HTTP

1) Update System
sudo dnf -y update

2) Install PHP 8.3, Nginx, and dependencies
Oracle Linux 9 may not provide PHP 8.3 in the default AppStream. Two options:

Option A — Use Remi’s PHP 8.3 (recommended)
sudo dnf -y install https://rpms.remirepo.net/enterprise/remi-release-9.rpm
sudo dnf -y module reset php
sudo dnf -y module enable php:remi-8.3
sudo dnf -y install nginx php php-fpm php-pdo php-sqlite3 php-mbstring php-json unzip git

Option B — Use distribution PHP (if 8.3 already available)
sudo dnf -y install nginx php php-fpm php-pdo php-sqlite3 php-mbstring php-json unzip git

3) Install Composer
Check if Composer exists:
composer --version

If not installed, use the official installer:
php -r "copy('https://getcomposer.org/installer', 'composer-setup.php');"
php composer-setup.php --install-dir=/usr/local/bin --filename=composer
php -r "unlink('composer-setup.php');"
composer --version

4) Obtain the application source
If you already have this code in your home repo, you can copy it to /var/www. Otherwise, clone a repository or transfer files.

Assuming the code is present under /home/opc/github/devspace/appstore-php8.3:
sudo mkdir -p /var/www
sudo rsync -a /home/opc/github/devspace/appstore-php8.3/ /var/www/appstore-php8.3/

5) Install PHP dependencies
cd /var/www/appstore-php8.3
composer install --no-interaction --no-dev --prefer-dist

This will create vendor/ and autoload files.

6) Initialize directories and permissions
Create writable directories for the app and set ownership to nginx:
sudo chown -R nginx:nginx /var/www/appstore-php8.3
sudo find /var/www/appstore-php8.3 -type d -exec chmod 755 {} \;
sudo find /var/www/appstore-php8.3 -type f -exec chmod 644 {} \;

Ensure database and logs directories are writable by PHP-FPM:
sudo mkdir -p /var/www/appstore-php8.3/database /var/www/appstore-php8.3/logs
sudo chown -R nginx:nginx /var/www/appstore-php8.3/database /var/www/appstore-php8.3/logs
sudo chmod 775 /var/www/appstore-php8.3/database /var/www/appstore-php8.3/logs
# Ensure application log file exists with correct ownership and permissions
sudo touch /var/www/appstore-php8.3/logs/app.log
sudo chown nginx:nginx /var/www/appstore-php8.3/logs/app.log
sudo chmod 664 /var/www/appstore-php8.3/logs/app.log

SELinux (if enforcing): either set correct contexts or temporarily test with permissive. Recommended contexts:
sudo chcon -R -t httpd_sys_rw_content_t /var/www/appstore-php8.3/database
sudo chcon -R -t httpd_sys_rw_content_t /var/www/appstore-php8.3/logs

7) Initialize SQLite database
Run the init script (creates tables, seeds user and products). It will create database/appstore.db:
cd /var/www/appstore-php8.3
php scripts/init_db.php

After running, re-apply ownership to ensure Nginx/PHP-FPM can write to the DB:
sudo chown -R nginx:nginx /var/www/appstore-php8.3/database

8) Nginx configuration
Create a server block at /etc/nginx/conf.d/appstore.conf:
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

9) PHP-FPM pool configuration
Create a dedicated pool (optional but recommended) at /etc/php-fpm.d/appstore.conf:
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

Note: If you already have a default pool (/etc/php-fpm.d/www.conf), ensure it’s compatible or disable it if you want to use only appstore pool. The listen socket path above matches the Nginx config.

10) Enable and restart services
sudo systemctl enable php-fpm
sudo systemctl enable nginx
sudo systemctl restart php-fpm
sudo systemctl restart nginx

11) Open firewall (if firewalld is active)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload

Network Security Note
- In this lab, ingress is restricted at the network/security list to your workstation’s IP (CIDR /32) for any port. This ensures only your test computer/laptop can reach the VM.
- Egress is allowed to 0.0.0.0/0 for outbound connectivity (e.g., package installs, updates).
- With server_name _ and this ingress rule, only requests originating from your /32 can access the site even though Nginx listens on :80.
- For production, consider limiting exposed ports and hardening security groups, and disable simulation endpoints if not required.

12) Validate the application
- Navigate to: http://<VM_IP>/
- You should see the login page at /login or be redirected there.
- Login with:
  - Username: admin
  - Password: demo123
- Browse products (/products), view details (/product/{id}), add to cart, update quantities, remove items, checkout (/checkout), and view order history (/orders).
- Simulation endpoints:
  - http://<VM_IP>/simulate/slow  (responds after 3–5 seconds)
  - http://<VM_IP>/simulate/error (HTTP 500 generated intentionally)

13) Logs and troubleshooting
- Application log: /var/www/appstore-php8.3/logs/app.log
- Nginx logs:
  - Access: /var/www/appstore-php8.3/logs/access.log
  - Error:  /var/www/appstore-php8.3/logs/nginx_error.log
- PHP-FPM error log: /var/www/appstore-php8.3/logs/php_error.log

Common issues:
- 403/500 due to SELinux contexts
  - Apply: chcon -R -t httpd_sys_rw_content_t /var/www/appstore-php8.3/{database,logs}
- Missing vendor/autoload.php
  - Run: composer install in /var/www/appstore-php8.3
- Database permission errors
  - Ensure nginx owns the DB: chown -R nginx:nginx /var/www/appstore-php8.3/database

14) Local development (optional)
If you just want to run locally without Nginx:
cd /var/www/appstore-php8.3
composer install
php scripts/init_db.php
composer start
Browse http://localhost:8080

15) Credentials
- Username: admin
- Password: demo123

16) Hardening tips (optional)
- Keep wildcard server_name _ if you rely on upstream security lists/NSGs restricting ingress to your /32; otherwise set an explicit FQDN/IP and adjust DNS/firewall accordingly.
- Nginx security headers (alternative to app-level headers already set in the app):
  Add inside your server block:
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
- Hide Nginx version banner:
  In /etc/nginx/nginx.conf under http { ... } add: server_tokens off;
- Rate-limit auth endpoints (optional):
  Consider limit_req_zone/limit_req for POST /login to mitigate brute force attempts.
- HTTPS/TLS:
  Terminate TLS at Nginx or an upstream LB; when behind TLS (or with HTTP_X_FORWARDED_PROTO=https), the app sets secure session cookies automatically.
- Production hygiene:
  Disable simulation endpoints (/simulate/*), and consider CSRF protection for POST forms and stricter Content-Security-Policy.

This completes the Phase 1 setup. The application is now ready for use and future instrumentation phases.
