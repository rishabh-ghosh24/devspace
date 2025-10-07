# PHP 8.3 Mini-Storefront with OCI APM

This is a PHP 8.3 application consisting of a storefront (with login) and a payment service, both instrumented for OpenTelemetry tracing to OCI APM.

## Features
- User authentication with session-based login
- Product browsing, cart management, checkout
- Mock payment processing
- Chaos engineering toggles
- Structured JSON logging
- OCI APM tracing

## Setup for Local Development

1. Ensure Docker and Docker Compose are installed.

2. Clone or navigate to the `app-store-php8.3` directory.

3. Build and run the services:
   ```
   docker-compose up --build
   ```

4. Access the application:
   - Storefront: http://localhost:8080
   - Payment (API): http://localhost:8081

## Credentials
- Username: `admin`
- Password: `securePass123`

## APM Configuration
Tracing uses Composer-based OpenTelemetry packages (no PECL extension needed for reliability). Set the following environment variables in `docker-compose.yml` or your deployment:

For Storefront:
```
OTEL_SERVICE_NAME=storefront
OTEL_RESOURCE_ATTRIBUTES=deployment.environment=dev,service.version=0.1.0
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_ENDPOINT=https://trace-ingestion.eu-frankfurt-1.oci.oraclecloud.com/20200101/opentelemetry/v1/traces
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Bearer <YOUR_APM_TOKEN>
```

For Payment:
```
OTEL_SERVICE_NAME=payment
OTEL_RESOURCE_ATTRIBUTES=deployment.environment=dev,service.version=0.1.0
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_ENDPOINT=https://trace-ingestion.eu-frankfurt-1.oci.oraclecloud.com/20200101/opentelemetry/v1/traces
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Bearer <YOUR_APM_TOKEN>
```

Trace context is injected into logs via TRACEPARENT header workaround (no PECL extension required).

## Testing
- Login with the provided credentials.
- Browse products, add to cart, checkout.
- Check logs in `storefront/logs/storefront.log` and `payment/logs/payment.log`.
- View traces in OCI APM console.

## Chaos Testing
Use headers like `X-Chaos-Latency: 500` to simulate delays.

## VM Deployment on Oracle Linux 9
For production deployment on your OL9 VM (adapted from build book, using Composer-only OTEL):

### Prerequisites
- OL9 VM with `sudo` access.
- APM access token from OCI APM console.
- Code copied to VM (e.g., `scp -r app-store-php8.3 user@vm:/home/user/`).

### Step 1: VM Bootstrap
```bash
sudo -i
dnf -y install nginx php php-fpm php-cli php-json php-mbstring php-pdo php-sqlite3 php-devel php-pear git unzip zip gcc make autoconf jq policycoreutils-python-utils
php -r "copy('https://getcomposer.org/installer', 'composer-setup.php');"
php composer-setup.php --install-dir=/usr/local/bin --filename=composer
rm -f composer-setup.php

# Create users and directories
useradd --system --home /var/www/storefront --shell /sbin/nologin storefront || true
useradd --system --home /var/www/payment   --shell /sbin/nologin payment   || true
mkdir -p /var/www/storefront/public /var/www/payment/public /var/lib/app /var/log/app /var/log/php-fpm
chown -R storefront:storefront /var/www/storefront
chown -R payment:payment       /var/www/payment
chown -R nginx:nginx /var/log/php-fpm
chown root:storefront /var/lib/app
chmod 0775 /var/lib/app

# SELinux
setsebool -P httpd_can_network_connect 1
semanage fcontext -a -t httpd_sys_rw_content_t "/var/lib/app(/.*)?"
semanage fcontext -a -t httpd_log_t "/var/log/app(/.*)?"
restorecon -Rv /var/lib/app /var/log/app
```

### Step 2: Deploy Code
```bash
cp -r /home/user/app-store-php8.3/storefront/* /var/www/storefront/
cp -r /home/user/app-store-php8.3/payment/* /var/www/payment/
cd /var/www/storefront && composer install --no-dev --optimize-autoloader
cd /var/www/payment && composer install --no-dev --optimize-autoloader
chown -R storefront:storefront /var/www/storefront
chown -R payment:payment /var/www/payment
```

### Step 3: Configure PHP-FPM with APM
Replace `<APM_TOKEN>` with your token:
```bash
# Storefront pool
cat > /etc/php-fpm.d/storefront.conf <<'CONF'
[storefront]
user = storefront
group = storefront
listen = /run/php-fpm-storefront.sock
listen.owner = nginx
listen.group = nginx
pm = dynamic
pm.max_children = 10
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 5

env[OTEL_SERVICE_NAME] = storefront
env[OTEL_RESOURCE_ATTRIBUTES] = deployment.environment=dev,service.version=0.1.0
env[OTEL_EXPORTER_OTLP_PROTOCOL] = http/protobuf
env[OTEL_EXPORTER_OTLP_ENDPOINT] = https://trace-ingestion.eu-frankfurt-1.oci.oraclecloud.com/20200101/opentelemetry/v1/traces
env[OTEL_EXPORTER_OTLP_HEADERS] = Authorization=Bearer <APM_TOKEN>

env[DB_PATH] = /var/lib/app/storefront.db
env[PAYMENT_BASE_URL] = http://127.0.0.1:8081
env[LOG_PATH] = /var/log/app/storefront.log

php_admin_value[error_log] = /var/log/php-fpm/storefront-error.log
php_admin_flag[log_errors] = on
CONF

# Payment pool
cat > /etc/php-fpm.d/payment.conf <<'CONF'
[payment]
user = payment
group = payment
listen = /run/php-fpm-payment.sock
listen.owner = nginx
listen.group = nginx
pm = dynamic
pm.max_children = 10
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 5

env[OTEL_SERVICE_NAME] = payment
env[OTEL_RESOURCE_ATTRIBUTES] = deployment.environment=dev,service.version=0.1.0
env[OTEL_EXPORTER_OTLP_PROTOCOL] = http/protobuf
env[OTEL_EXPORTER_OTLP_ENDPOINT] = https://trace-ingestion.eu-frankfurt-1.oci.oraclecloud.com/20200101/opentelemetry/v1/traces
env[OTEL_EXPORTER_OTLP_HEADERS] = Authorization=Bearer <APM_TOKEN>

env[LOG_PATH] = /var/log/app/payment.log

php_admin_value[error_log] = /var/log/php-fpm/payment-error.log
php_admin_flag[log_errors] = on
CONF

systemctl enable --now php-fpm
systemctl restart php-fpm
```

### Step 4: Configure Nginx
```bash
# Storefront vhost
cat > /etc/nginx/conf.d/storefront.conf <<'CONF'
server {
  listen 127.0.0.1:8080;
  server_name localhost;
  root /var/www/storefront/public;
  index index.php;
  access_log /var/log/nginx/storefront.access.json main;
  error_log /var/log/nginx/storefront.error.log;
  location / { try_files $uri /index.php$is_args$args; }
  location ~ \.php$ {
    include fastcgi_params;
    fastcgi_param SCRIPT_FILENAME $document_root/index.php;
    fastcgi_pass unix:/run/php-fpm-storefront.sock;
  }
}
CONF

# Payment vhost
cat > /etc/nginx/conf.d/payment.conf <<'CONF'
server {
  listen 127.0.0.1:8081;
  server_name localhost;
  root /var/www/payment/public;
  index index.php;
  access_log /var/log/nginx/payment.access.json main;
  error_log /var/log/nginx/payment.error.log;
  location / { try_files $uri /index.php$is_args$args; }
  location ~ \.php$ {
    include fastcgi_params;
    fastcgi_param SCRIPT_FILENAME $document_root/index.php;
    fastcgi_pass unix:/run/php-fpm-payment.sock;
  }
}
CONF

# JSON log format
if ! grep -q 'log_format main' /etc/nginx/nginx.conf; then
  sed -i '/http {/a \\tlog_format main escape=json \'{\"time\":\"$time_iso8601\",\"remote\":\"$remote_addr\",\"host\":\"$host\",\"req\":\"$request\",\"status\":$status,\"bytes\":$body_bytes_sent,\"ref\":\"$http_referer\",\"ua\":\"$http_user_agent\",\"rt\":$request_time}\";\'' /etc/nginx/nginx.conf
fi

systemctl enable --now nginx
systemctl restart nginx
```

### Step 5: Initialize and Test
```bash
# Seed DB
su - storefront -c 'cd /var/www/storefront && php -r "require \"vendor/autoload.php\"; $db = App\Db::connect(\"/var/lib/app/storefront.db\"); App\Db::migrateStorefront(\$db); echo \"DB ready\n\";"'

# Health checks
curl -s http://127.0.0.1:8080/health | jq .
curl -s http://127.0.0.1:8081/health | jq .

# Access storefront at http://127.0.0.1:8080, login with admin/securePass123
# Check logs and APM console for traces
```

(Note: No PECL extension installed for reliability. OTEL packages handle tracing.)
