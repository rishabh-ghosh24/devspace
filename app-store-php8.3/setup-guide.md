# Complete Setup Guide: PHP 8.3 Mini-Storefront with OCI APM on Oracle Linux 9

This guide provides step-by-step instructions to deploy the PHP 8.3 mini-storefront application with OCI APM auto-instrumentation on an Oracle Linux 9 compute instance. The app includes login, product browsing, cart, checkout, and payment simulation.

## Prerequisites
- Oracle Linux 9 VM with `sudo` access.
- OCI APM access token (from OCI Console → APM → Access Tokens).
- GitHub repository access (use PAT for private repos).
- Basic familiarity with Linux commands.

## Overview
- **Services**: Storefront (port 8080, web UI) and Payment (port 8081, API).
- **Tech Stack**: PHP 8.3, Slim 4, Twig, SQLite, Nginx, PHP-FPM, OpenTelemetry (Composer-based).
- **Features**: User auth, e-commerce flow, chaos testing, JSON logging, APM tracing.
- **Access**: http://<vm-public-ip>:8080 (login: admin/securePass123).

## Step 1: System Setup and PHP 8.3 Installation
Update the system and install PHP 8.3 using Remi's repository (since OL9 default is PHP 8.0).

```bash
sudo -i
dnf update -y
dnf install -y oraclelinux-developer-release-el9
dnf config-manager --set-enabled ol9_developer
dnf install -y nginx php php-fpm php-cli php-json php-mbstring php-pdo php-sqlite3 php-devel php-pear
dnf install -y https://rpms.remirepo.net/enterprise/remi-release-9.rpm
dnf module enable -y php:remi-8.3
dnf remove -y php*
dnf install -y php php-fpm php-cli php-json php-mbstring php-pdo php-sqlite3 php-devel php-pear
alternatives --set php /usr/bin/php83
alternatives --set php-fpm /usr/lib/systemd/system/php83-php-fpm.service
php --version  # Verify 8.3.x
```

Install Composer and additional tools:

```bash
php -r "copy('https://getcomposer.org/installer', 'composer-setup.php');"
php composer-setup.php --install-dir=/usr/local/bin --filename=composer
rm -f composer-setup.php
export PATH=$PATH:/usr/local/bin
echo 'export PATH=$PATH:/usr/local/bin' >> ~/.bashrc
composer --version  # Verify
dnf install -y git unzip zip gcc make autoconf jq policycoreutils-python-utils
```

## Step 2: Create Users, Directories, and SELinux Configuration
Set up isolated users and directories for security.

```bash
useradd --system --home /var/www/storefront --shell /sbin/nologin storefront || true
useradd --system --home /var/www/payment --shell /sbin/nologin payment || true
mkdir -p /var/www/storefront/public /var/www/payment/public /var/lib/app /var/log/app /var/log/php-fpm
chown -R storefront:storefront /var/www/storefront
chown -R payment:payment /var/www/payment
chown -R nginx:nginx /var/log/php-fpm
chown root:storefront /var/lib/app
chmod 0775 /var/lib/app
setsebool -P httpd_can_network_connect 1
semanage fcontext -a -t httpd_sys_rw_content_t "/var/lib/app(/.*)?"
semanage fcontext -a -t httpd_log_t "/var/log/app(/.*)?"
restorecon -Rv /var/lib/app /var/log/app
```

## Step 3: Deploy Application Code
Clone the repo and install dependencies.

```bash
# Create PAT in GitHub: Settings → Developer → Personal Access Tokens → Generate classic token (scope: repo)
git clone https://<username>:<PAT>@github.com/rishabh-ghosh24/devspace.git /tmp/devspace
cp -r /tmp/devspace/app-store-php8.3/storefront/* /var/www/storefront/
cp -r /tmp/devspace/app-store-php8.3/payment/* /var/www/payment/
cd /var/www/storefront && composer install --no-dev --optimize-autoloader
cd /var/www/payment && composer install --no-dev --optimize-autoloader
chown -R storefront:storefront /var/www/storefront
chown -R payment:payment /var/www/payment
```

## Step 4: Configure PHP-FPM Pools with APM Auto-Instrumentation
Set up PHP-FPM for both services. APM tracing uses Composer packages (no PECL extension).

Replace `<APM_TOKEN>` with your OCI APM token. Uncomment OTEL lines for tracing.

```bash
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

# APM Auto-Instrumentation (uncomment to enable tracing)
# env[OTEL_SERVICE_NAME]=storefront
# env[OTEL_RESOURCE_ATTRIBUTES]=deployment.environment=dev,service.version=0.1.0
# env[OTEL_EXPORTER_OTLP_PROTOCOL]=http/protobuf
# env[OTEL_EXPORTER_OTLP_ENDPOINT]=https://trace-ingestion.eu-frankfurt-1.oci.oraclecloud.com/20200101/opentelemetry/v1/traces
# env[OTEL_EXPORTER_OTLP_HEADERS]="Authorization=Bearer <APM_TOKEN>"

env[DB_PATH]=/var/lib/app/storefront.db
env[PAYMENT_BASE_URL]=http://127.0.0.1:8081
env[LOG_PATH]=/var/log/app/storefront.log
php_admin_value[error_log]=/var/log/php-fpm/storefront-error.log
php_admin_flag[log_errors]=on
CONF

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

# APM Auto-Instrumentation (uncomment to enable tracing)
# env[OTEL_SERVICE_NAME]=payment
# env[OTEL_RESOURCE_ATTRIBUTES]=deployment.environment=dev,service.version=0.1.0
# env[OTEL_EXPORTER_OTLP_PROTOCOL]=http/protobuf
# env[OTEL_EXPORTER_OTLP_ENDPOINT]=https://trace-ingestion.eu-frankfurt-1.oci.oraclecloud.com/20200101/opentelemetry/v1/traces
# env[OTEL_EXPORTER_OTLP_HEADERS]="Authorization=Bearer <APM_TOKEN>"

env[LOG_PATH]=/var/log/app/payment.log
php_admin_value[error_log]=/var/log/php-fpm/payment-error.log
php_admin_flag[log_errors]=on
CONF

systemctl enable php-fpm
systemctl start php-fpm
systemctl status php-fpm
```

## Step 5: Configure Nginx Web Server
Set up Nginx to serve the app externally on port 8080.

```bash
cat > /etc/nginx/conf.d/storefront.conf <<'CONF'
server {
  listen 8080;
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

# Add JSON log format
if ! grep -q 'log_format main' /etc/nginx/nginx.conf; then
  sed -i '/http {/a \\tlog_format main escape=json \'{\"time\":\"$time_iso8601\",\"remote\":\"$remote_addr\",\"host\":\"$host\",\"req\":\"$request\",\"status\":$status,\"bytes\":$body_bytes_sent\",\"ref\":\"$http_referer\",\"ua\":\"$http_user_agent\",\"rt\":$request_time}\";\'' /etc/nginx/nginx.conf
fi

systemctl enable nginx
systemctl start nginx
systemctl status nginx
```

## Step 6: Configure Firewall and SELinux for External Access
Allow external traffic to port 8080.

```bash
firewall-cmd --add-port=8080/tcp --permanent
firewall-cmd --reload
firewall-cmd --list-all  # Verify 8080/tcp added
semanage port -a -t http_port_t -p tcp 8080
```

## Step 7: OCI VCN Security List
Ensure the subnet's security list allows ingress:
- Source Type: CIDR
- Source CIDR: 0.0.0.0/0 (or your laptop IP range)
- IP Protocol: TCP
- Destination Port Range: 8080

## Step 8: Initialize Database and Test
Set up the DB and verify the app.

```bash
cd /var/www/storefront && php -r "require 'vendor/autoload.php'; \$db = App\Db::connect('/var/lib/app/storefront.db'); App\Db::migrateStorefront(\$db); echo 'DB ready\n';"
curl -s http://127.0.0.1:8080/health | jq .  # {"status":"ok",...}
curl -s http://127.0.0.1:8081/health | jq .  # {"status":"ok",...}
```

## Step 9: Access and Test the Application
- **URL**: http://<vm-public-ip>:8080
- **Login**: admin / securePass123
- **Test Flow**:
  1. Login.
  2. Browse products (Widget, Gadget, Doodad).
  3. Add to cart (AJAX updates).
  4. View cart.
  5. Checkout (enter card last 4 digits, e.g., 4242).
  6. View order confirmation.
- **Logs**: Check `/var/log/app/storefront.log` and `/var/log/app/payment.log` for JSON logs with trace IDs.

## Enabling OCI APM Tracing
1. Uncomment OTEL env vars in `/etc/php-fpm.d/storefront.conf` and `/etc/php-fpm.d/payment.conf`.
2. Replace `<APM_TOKEN>` with your token.
3. `systemctl restart php-fpm`.
4. Generate traffic (e.g., checkout).
5. Check OCI APM Console → Traces for spans (login, DB queries, API calls).

## Troubleshooting
- **PHP-FPM fails**: Check `/var/log/php-fpm/*.log` for env var errors (quote values with spaces).
- **Nginx not binding externally**: Ensure `listen 8080;` (not `127.0.0.1:8080`), reload nginx, check `netstat -tlnp | grep 8080`.
- **Firewall blocks**: `firewall-cmd --list-all` should show 8080/tcp.
- **SELinux blocks**: `semanage port -l | grep 8080` should show http_port_t.
- **OCI access denied**: Verify security list ingress for TCP 8080.
- **DB read-only errors (e.g., add to cart fails)**: If DB owned by root, run `chown storefront:storefront /var/lib/app/storefront.db && chmod 664 /var/lib/app/storefront.db`.
- **APM no traces**: Ensure token is valid, OTEL vars unquoted, check APM domain/region.

## Chaos Testing
Add headers to requests for testing:
- `X-Chaos-Latency: 1000` (add 1s delay).
- `X-Chaos-Error-Rate: 0.5` (50% error chance).

The app is now fully deployed and observable with APM!
