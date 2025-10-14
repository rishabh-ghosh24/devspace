<?php
declare(strict_types=1);

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Slim\Factory\AppFactory;

require __DIR__ . '/../vendor/autoload.php';

define('ROOT_DIR', dirname(__DIR__));

// Load settings first (for session config)
$settingsFactory = require ROOT_DIR . '/config/settings.php';
$settings = $settingsFactory();

// Configure secure session cookie parameters before starting the session
if (PHP_SESSION_ACTIVE !== session_status()) {
    if (!empty($settings['app']['session_name'])) {
        session_name($settings['app']['session_name']);
    }
    $secure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
        || (isset($_SERVER['HTTP_X_FORWARDED_PROTO']) && $_SERVER['HTTP_X_FORWARDED_PROTO'] === 'https');
    session_set_cookie_params([
        'lifetime' => 0,
        'path' => '/',
        'domain' => '',
        'secure' => $secure,           // true if HTTPS/behind TLS, false otherwise
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
    session_start();
}

$loggerFactory = require ROOT_DIR . '/config/logger.php';
$logger = $loggerFactory($settings);

$dbFactory = require ROOT_DIR . '/config/database.php';
$pdo = $dbFactory($settings, $logger);

// Plates template engine
$templates = new League\Plates\Engine(ROOT_DIR . '/src/views');

// Slim app
$app = AppFactory::create();
$app->addRoutingMiddleware();
$app->addBodyParsingMiddleware();

// Add simple security headers (non-breaking)
$app->add(function (Request $request, $handler) {
    $response = $handler->handle($request);
    return $response
        ->withHeader('X-Frame-Options', 'SAMEORIGIN')
        ->withHeader('X-Content-Type-Options', 'nosniff')
        ->withHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
});

// Error handling
$displayErrors = (bool)($settings['displayErrorDetails'] ?? false);
$errorMiddleware = $app->addErrorMiddleware($displayErrors, true, true, $logger);

// Simple DI container array
$container = [
    'settings' => $settings,
    'logger' => $logger,
    'db' => $pdo,
    'templates' => $templates,
];

 // Expose $app and services to routes file
$GLOBALS['app'] = $app;
$GLOBALS['container'] = $container;
// Routes
require ROOT_DIR . '/src/routes/web.php';

// Fallback health check if routes file is missing
if (!isset($GLOBALS['__routes_loaded'])) {
    $app->get('/health', function (Request $request, Response $response) {
        $response->getBody()->write(json_encode(['status' => 'ok']));
        return $response->withHeader('Content-Type', 'application/json');
    });
}

$app->run();
