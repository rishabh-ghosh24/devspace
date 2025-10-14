# appstore-php8.3 (Phase 1 - MVP)

Lightweight PHP 8.3 storefront built with Slim 4, Plates templating, and SQLite. This MVP provides a realistic e-commerce flow without any APM or Logging Analytics instrumentation.

Features:
- Demo login (admin / demo123) using SQLite
- Product list and detail pages
- Session-based shopping cart (add/update/remove)
- Checkout with persisted orders and order items
- Order history for the logged-in user
- Simulation endpoints:
  - /simulate/slow (3–5s delay)
  - /simulate/error (HTTP 500)
- Monolog application logging to logs/app.log

Stack:
- PHP 8.3, Slim 4, slim/psr7
- Plates templates
- SQLite (PDO)
- Nginx + PHP-FPM (deployment) or PHP built-in server (dev)

Project Layout:
- public/index.php — Slim front controller
- src/controllers, src/models, src/views — MVC-ish app structure
- src/routes/web.php — All routes
- config/settings.php, config/database.php, config/logger.php — App config
- scripts/init_db.php — Create schema and seed demo data
- database/appstore.db — SQLite DB (created by init script)
- logs/app.log — Application log

Local Development (PHP built-in server)
- Install dependencies: composer install
- Initialize database: php scripts/init_db.php
- Start dev server: composer start
- Navigate: http://localhost:8080

Deployment
- Uses Nginx + PHP-FPM via unix socket (fastcgi_pass unix:/run/php-fpm/appstore.sock) and wildcard server_name _ by default.
- See setup.md for full Oracle Linux + Nginx/PHP-FPM steps, permissions, SELinux notes, and the Network Security Note about restricting ingress to your /32 and allowing egress 0.0.0.0/0.

Credentials
- Username: admin
- Password: demo123

Security considerations
- Sessions: Cookies are HttpOnly and SameSite=Lax; the “secure” flag is enabled automatically when served over HTTPS or when HTTP_X_FORWARDED_PROTO=https is present. Configure TLS/termination for production.
- Errors: displayErrorDetails is false by default; enable only temporarily for debugging.
- Inputs: Controllers cast IDs and quantities to integers; database access uses prepared statements (PDO) to mitigate SQL injection.
- Filesystem: Ensure logs/ and database/ are writable by the php-fpm user (nginx) and carry proper SELinux contexts on enforcing systems.
- Network: In lab environments we recommend restricting ingress to your workstation’s public IP (/32) and leaving egress to 0.0.0.0/0 for updates. With server_name _ and restricted ingress, only your /32 can reach the app.
- Hardening (future): add CSRF tokens for POSTs, rate limiting for auth routes, stricter Content-Security-Policy, and disable simulation endpoints in production.

License
MIT (see repository license)
