# appstore-php8.3 (Phase 1 - MVP)

A lightweight PHP 8.3 storefront built with Slim 4, Plates templating, and SQLite. This MVP provides a realistic but simple e-commerce flow that can be used for various testing use cases.

## Overview

This demo application was created to monitor a PHP 8+ app with Oracle Application Performance Monitoring (APM) and OpenTelemetry with auto-instrumentation support for collecting application traces. Logs will be collected and analyzed using OCI Log Analytics (LA), but these monitoring components will not be included here. Instead, they will be added under a separate project in Phase 2, named **appstore-php8.3-observability**.

---

## Features

- Demo login using SQLite authentication
- Product list and detail pages
- Session-based shopping cart with add, update, and remove functionality
- Checkout with persisted orders and order items
- Order history for logged-in users
- Simulation endpoints for testing:
  - `/simulate/slow` - 3-5 second delay
  - `/simulate/error` - HTTP 500 response
- Monolog application logging to `logs/app.log`

---

## Technology Stack

- **PHP 8.3** - Core language
- **Slim 4** - Micro-framework with slim/psr7
- **Plates** - Native PHP template engine
- **SQLite** - Database with PDO
- **Nginx + PHP-FPM** - Production deployment
- **PHP Built-in Server** - Local development

---

## Project Structure

```
appstore-php8.3/
├── public/
│   └── index.php              # Slim front controller
├── src/
│   ├── controllers/           # Controller classes
│   ├── models/                # Model classes
│   ├── views/                 # Plates templates
│   └── routes/
│       └── web.php            # Application routes
├── config/
│   ├── settings.php           # Application settings
│   ├── database.php           # Database configuration
│   └── logger.php             # Logging configuration
├── scripts/
│   └── init_db.php            # Database schema and seeding
├── database/
│   └── appstore.db            # SQLite database (created by init script)
└── logs/
    └── app.log                # Application log file
```

---

## Getting Started

### Local Development

Use PHP's built-in server for quick local development:

1. **Install dependencies:**
   ```bash
   composer install
   ```

2. **Initialize database:**
   ```bash
   php scripts/init_db.php
   ```

3. **Start development server:**
   ```bash
   composer start
   ```

4. **Navigate to:**
   ```
   http://localhost:8080
   ```

### Production Deployment

For production deployment with Nginx and PHP-FPM:

- Uses Nginx with PHP-FPM via unix socket (`fastcgi_pass unix:/run/php-fpm/appstore.sock`)
- Wildcard `server_name _` by default
- See `setup.md` for complete Oracle Linux + Nginx/PHP-FPM installation steps, including:
  - Permissions configuration
  - SELinux contexts
  - Network security notes about restricting ingress to your /32 and allowing egress to 0.0.0.0/0

---

## Default Credentials

- **Username:** `admin`
- **Password:** `demo123`

---

## Security Considerations

### Sessions

- Cookies are set with `HttpOnly` and `SameSite=Lax` flags
- The `Secure` flag is enabled automatically when:
  - Served over HTTPS, or
  - `HTTP_X_FORWARDED_PROTO=https` header is present
- Configure TLS termination for production environments

### Error Handling

- `displayErrorDetails` is set to `false` by default
- Enable only temporarily for debugging purposes

### Input Validation

- Controllers cast IDs and quantities to integers
- Database access uses prepared statements (PDO) to mitigate SQL injection

### Filesystem Security

- Ensure `logs/` and `database/` directories are writable by the PHP-FPM user (typically `nginx`)
- Apply proper SELinux contexts on enforcing systems

### Network Security

In lab environments:

- Restrict ingress to your workstation's public IP (/32)
- Allow egress to 0.0.0.0/0 for package updates
- With `server_name _` and restricted ingress, only your /32 can reach the application

### Future Hardening

Consider implementing the following for production:

- CSRF tokens for POST requests
- Rate limiting for authentication routes
- Stricter Content-Security-Policy headers
- Disable simulation endpoints

---

## License

MIT (see repository license)

---

## Related Projects

- Phase 2 - **appstore-php8.3-observability** - Monitoring and observability instrumentation using OCI Application Performance Monitoring and OCI Log Analytics (coming soon)
