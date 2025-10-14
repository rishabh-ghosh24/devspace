<?php
declare(strict_types=1);

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

use App\controllers\AuthController;
use App\controllers\ProductController;
use App\controllers\CartController;
use App\controllers\OrderController;
use App\controllers\SimulationController;
use App\helpers\Session;

/** @var \Slim\App $app */
global $app;
/** @var array $container */
global $container;

$GLOBALS['__routes_loaded'] = true;

// Controllers
$authController = new AuthController($container['db'], $container['logger'], $container['templates']);
$productController = new ProductController($container['db'], $container['logger'], $container['templates']);
$cartController = new CartController($container['db'], $container['logger'], $container['templates']);
$orderController = new OrderController($container['db'], $container['logger'], $container['templates']);
$simulationController = new SimulationController($container['logger']);

// Simple auth middleware
$requireAuth = function (Request $request, Response $response, callable $next) {
    if (!Session::isAuthenticated()) {
        return $response
            ->withHeader('Location', '/login')
            ->withStatus(302);
    }
    return $next($request, $response);
};

// Root -> redirect based on auth
$app->get('/', function (Request $request, Response $response) {
    if (Session::isAuthenticated()) {
        return $response->withHeader('Location', '/products')->withStatus(302);
    }
    return $response->withHeader('Location', '/login')->withStatus(302);
});

// Auth
$app->get('/login', [$authController, 'loginPage']);
$app->post('/login', [$authController, 'login']);
$app->get('/logout', [$authController, 'logout']);

// Products (public)
$app->get('/products', [$productController, 'index']);
$app->get('/product/{id}', [$productController, 'detail']);

// Cart
$app->post('/cart/add', [$cartController, 'add']);
$app->get('/cart', [$cartController, 'view']);
$app->post('/cart/update', [$cartController, 'update']);
$app->post('/cart/remove', [$cartController, 'remove']);

// Orders (require auth)
$app->post('/checkout', function (Request $request, Response $response) use ($orderController, $requireAuth) {
    return $requireAuth($request, $response, fn($req, $res) => $orderController->checkout($req, $res));
});
$app->get('/orders', function (Request $request, Response $response) use ($orderController, $requireAuth) {
    return $requireAuth($request, $response, fn($req, $res) => $orderController->history($req, $res));
});

// Simulation
$app->get('/simulate/slow', [$simulationController, 'slow']);
$app->get('/simulate/error', [$simulationController, 'error']);
