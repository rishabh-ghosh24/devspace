<?php
declare(strict_types=1);

namespace App\controllers;

use App\helpers\Session;
use App\models\UserModel;
use League\Plates\Engine;
use Monolog\Logger;
use PDO;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

class AuthController
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

    public function loginPage(Request $request, Response $response): Response
    {
        if (Session::isAuthenticated()) {
            return $response->withHeader('Location', '/products')->withStatus(302);
        }
        return $this->render($response, 'auth/login', [
            'title' => 'Login',
            'error' => null,
        ]);
    }

    public function login(Request $request, Response $response): Response
    {
        $data = (array)$request->getParsedBody();
        $username = trim((string)($data['username'] ?? ''));
        $password = (string)($data['password'] ?? '');

        $model = new UserModel($this->db);
        $user = $model->findByUsername($username);

        if ($user && password_verify($password, $user['password_hash'])) {
            Session::login((int)$user['id'], (string)$user['username']);
            $this->logger->info('User logged in', ['user' => $username]);
            return $response->withHeader('Location', '/products')->withStatus(302);
        }

        $this->logger->warning('Login failed', ['user' => $username]);
        return $this->render($response, 'auth/login', [
            'title' => 'Login',
            'error' => 'Invalid username or password.',
            'old' => ['username' => htmlspecialchars($username, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')],
        ]);
    }

    public function logout(Request $request, Response $response): Response
    {
        $username = Session::username();
        Session::logout();
        $this->logger->info('User logged out', ['user' => $username]);
        return $response->withHeader('Location', '/login')->withStatus(302);
    }
}
