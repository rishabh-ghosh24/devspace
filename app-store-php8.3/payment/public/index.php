<?php
declare(strict_types=1);

use Slim\Factory\AppFactory;
use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Message\ResponseInterface as Response;
use Pay\Chaos;
use Pay\Log;

require __DIR__ . '/../vendor/autoload.php';

$app = AppFactory::create();
$app->addBodyParsingMiddleware();

$serviceName = 'payment';
$env = [
  'LOG_PATH' => getenv('LOG_PATH') ?: __DIR__ . '/../logs/payment.log',
  'CHAOS_DEFAULT_LATENCY_MS' => (int)(getenv('CHAOS_DEFAULT_LATENCY_MS') ?: 0),
  'CHAOS_DEFAULT_ERROR_RATE' => (float)(getenv('CHAOS_DEFAULT_ERROR_RATE') ?: 0.0),
];

$log = Log::create($serviceName, $env['LOG_PATH']);
$chaos = new Chaos($env['CHAOS_DEFAULT_LATENCY_MS'], $env['CHAOS_DEFAULT_ERROR_RATE']);

$app->add(function(Request $req, $handler) use ($chaos, $log) {
  $chaos->maybeSleep($req->getHeaderLine('X-Chaos-Latency'));
  $chaos->maybeError($req->getHeaderLine('X-Chaos-Error-Rate'), $req->getHeaderLine('X-Chaos-Force-Error'));
  try { $res = $handler->handle($req); }
  catch (\Throwable $e) { $log->error('unhandled_exception', ['exception'=>$e->getMessage()]); throw $e; }
  if (function_exists('opentelemetry_get_trace_id')) {
    $traceId = opentelemetry_get_trace_id();
    if ($traceId) $res = $res->withHeader('X-Trace-Id', $traceId);
  }
  return $res;
});

$app->get('/health', function(Request $req, Response $res) use ($serviceName) {
  $res->getBody()->write(json_encode(['status'=>'ok','service'=>$serviceName,'time'=>gmdate('c')]));
  return $res->withHeader('Content-Type','application/json');
});

$app->post('/pay', function(Request $req, Response $res) use ($log) {
  $body = (array)$req->getParsedBody();
  $orderId = (int)($body['order_id'] ?? 0);
  $amount  = (int)($body['amount'] ?? 0);
  $last4   = (string)($body['card_last4'] ?? '0000');

  if (strtolower($req->getHeaderLine('X-Chaos-Reject')) === 'card') {
    $res->getBody()->write(json_encode(['status'=>'DECLINED','reason'=>'Card rejected']));
    return $res->withHeader('Content-Type','application/json');
  }

  $log->info('payment_attempt', ['order_id'=>$orderId,'amount'=>$amount,'card_last4'=>$last4]);

  $ref = 'pay_' . bin2hex(random_bytes(4));
  $res->getBody()->write(json_encode(['status'=>'APPROVED','gateway_ref'=>$ref,'processed_at'=>gmdate('c')]));
  return $res->withHeader('Content-Type','application/json');
});

$app->run();
