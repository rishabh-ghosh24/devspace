<?php
declare(strict_types=1);

namespace App\controllers;

use Monolog\Logger;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

class SimulationController
{
    public function __construct(private Logger $logger)
    {
    }

    public function slow(Request $request, Response $response): Response
    {
        $delay = random_int(3, 5);
        $this->logger->info('Simulating slow endpoint', ['delay_sec' => $delay]);
        sleep($delay);

        $payload = json_encode(['status' => 'ok', 'delay_sec' => $delay], JSON_THROW_ON_ERROR);
        $response->getBody()->write($payload);
        return $response->withHeader('Content-Type', 'application/json');
    }

    public function error(Request $request, Response $response): Response
    {
        $this->logger->error('Simulating error endpoint');
        // Throwing an exception to trigger Slim error handler (HTTP 500)
        throw new \RuntimeException('Simulated server error');
    }
}
