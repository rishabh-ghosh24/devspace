<?php
declare(strict_types=1);

namespace App\controllers;

use App\helpers\Session;
use App\models\ProductModel;
use League\Plates\Engine;
use Monolog\Logger;
use PDO;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

class CartController
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

    public function add(Request $request, Response $response): Response
    {
        $data = (array)$request->getParsedBody();
        $productId = (int)($data['product_id'] ?? 0);
        $qty = max(1, (int)($data['qty'] ?? 1));

        $pm = new ProductModel($this->db);
        $product = $pm->find($productId);
        if (!$product) {
            $this->logger->warning('Attempt to add missing product to cart', ['id' => $productId]);
            return $response->withHeader('Location', '/products')->withStatus(302);
        }

        Session::addToCart($productId, $product['name'], (float)$product['price'], $qty);
        $this->logger->info('Added to cart', ['product' => $productId, 'qty' => $qty]);

        return $response->withHeader('Location', '/cart')->withStatus(302);
    }

    public function view(Request $request, Response $response): Response
    {
        $cart = Session::getCart();
        $total = 0.0;
        foreach ($cart as $line) {
            $total += (float)$line['price'] * (int)$line['qty'];
        }

        return $this->render($response, 'cart/index', [
            'title' => 'Your Cart',
            'cart' => $cart,
            'total' => $total,
            'isAuthenticated' => Session::isAuthenticated(),
            'username' => Session::username(),
        ]);
    }

    public function update(Request $request, Response $response): Response
    {
        $data = (array)$request->getParsedBody();
        $productId = (int)($data['product_id'] ?? 0);
        $qty = (int)($data['qty'] ?? 1);

        Session::updateQty($productId, $qty);
        $this->logger->info('Cart updated', ['product' => $productId, 'qty' => $qty]);

        return $response->withHeader('Location', '/cart')->withStatus(302);
    }

    public function remove(Request $request, Response $response): Response
    {
        $data = (array)$request->getParsedBody();
        $productId = (int)($data['product_id'] ?? 0);

        Session::removeFromCart($productId);
        $this->logger->info('Removed from cart', ['product' => $productId]);

        return $response->withHeader('Location', '/cart')->withStatus(302);
    }
}
