<?php
declare(strict_types=1);

namespace App\controllers;

use App\helpers\Session;
use App\models\OrderModel;
use League\Plates\Engine;
use Monolog\Logger;
use PDO;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

class OrderController
{
    public function __construct(
        private PDO $db,
        private Logger $logger,
        private Engine $templates
    ) {
    }

    private function render(Response $response, string $template, array $data = []): Response
    {
        $html = $this->templates->render($template, $data);
        $response->getBody()->write($html);
        return $response->withHeader('Content-Type', 'text/html');
    }

    public function checkout(Request $request, Response $response): Response
    {
        $userId = Session::userId();
        if ($userId === null) {
            return $response->withHeader('Location', '/login')->withStatus(302);
        }

        $cart = Session::getCart();
        if (empty($cart)) {
            $this->logger->warning('Checkout attempted with empty cart', ['user' => $userId]);
            return $response->withHeader('Location', '/cart')->withStatus(302);
        }

        $orders = new OrderModel($this->db);
        $orderId = $orders->createOrder($userId, $cart);

        Session::clearCart();
        $this->logger->info('Order created', ['user' => $userId, 'orderId' => $orderId]);

        return $response->withHeader('Location', '/orders')->withStatus(302);
    }

    public function history(Request $request, Response $response): Response
    {
        $userId = Session::userId();
        if ($userId === null) {
            return $response->withHeader('Location', '/login')->withStatus(302);
        }

        $orders = new OrderModel($this->db);
        $list = $orders->getOrdersWithItemsByUser($userId);

        return $this->render($response, 'orders/index', [
            'title' => 'Your Orders',
            'orders' => $list,
            'isAuthenticated' => true,
            'username' => Session::username(),
        ]);
    }
}
