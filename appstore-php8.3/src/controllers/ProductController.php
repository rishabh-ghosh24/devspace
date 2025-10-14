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

class ProductController
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

    public function index(Request $request, Response $response): Response
    {
        $model = new ProductModel($this->db);
        $products = $model->all();

        return $this->render($response, 'products/list', [
            'title' => 'Products',
            'products' => $products,
            'isAuthenticated' => Session::isAuthenticated(),
            'username' => Session::username(),
        ]);
    }

    public function detail(Request $request, Response $response, array $args): Response
    {
        $id = (int)($args['id'] ?? 0);
        $model = new ProductModel($this->db);
        $product = $model->find($id);

        if (!$product) {
            $this->logger->warning('Product not found', ['id' => $id]);
            $response = $response->withStatus(404);
            return $this->render($response, 'products/detail', [
                'title' => 'Product Not Found',
                'product' => null,
                'isAuthenticated' => Session::isAuthenticated(),
                'username' => Session::username(),
            ]);
        }

        return $this->render($response, 'products/detail', [
            'title' => $product['name'],
            'product' => $product,
            'isAuthenticated' => Session::isAuthenticated(),
            'username' => Session::username(),
        ]);
    }
}
