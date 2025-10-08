<?php
declare(strict_types=1);

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Slim\Factory\AppFactory;
use Twig\Environment;
use Twig\Loader\FilesystemLoader;
use App\Chaos;
use App\Log;
use App\Db;
use App\Auth;

require __DIR__ . '/../vendor/autoload.php';

$app = AppFactory::create();
$app->addBodyParsingMiddleware();

$serviceName = 'storefront';
$env = [
  'DB_PATH' => getenv('DB_PATH') ?: __DIR__ . '/../data/storefront.db',
  'PAYMENT_BASE_URL' => getenv('PAYMENT_BASE_URL') ?: 'http://127.0.0.1:8081',
  'LOG_PATH' => getenv('LOG_PATH') ?: __DIR__ . '/../logs/storefront.log',
  'CHAOS_DEFAULT_LATENCY_MS' => (int)(getenv('CHAOS_DEFAULT_LATENCY_MS') ?: 0),
  'CHAOS_DEFAULT_ERROR_RATE' => (float)(getenv('CHAOS_DEFAULT_ERROR_RATE') ?: 0.0),
];

$log = Log::create($serviceName, $env['LOG_PATH']);
$db  = Db::connect($env['DB_PATH']);
Db::migrateStorefront($db);

$chaos = new Chaos($env['CHAOS_DEFAULT_LATENCY_MS'], $env['CHAOS_DEFAULT_ERROR_RATE']);

// Twig setup
$loader = new FilesystemLoader(__DIR__ . '/../templates');
$twig = new Environment($loader);

// CSRF token generation
$csrfToken = bin2hex(random_bytes(32));

// Middleware for chaos and tracing
$app->add(function (Request $req, $handler) use ($chaos, $log) {
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

// Auth middleware
$authMiddleware = function (Request $req, $handler) {
  Auth::requireLogin();
  return $handler->handle($req);
};

// Helper function to render Twig
function renderTwig(Environment $twig, string $template, array $data = []): string {
  $data['user'] = Auth::isLoggedIn() ? ['username' => Auth::getUsername()] : null;
  $data['csrf_token'] = $GLOBALS['csrfToken'];
  $data['flash'] = $_SESSION['flash'] ?? null;
  unset($_SESSION['flash']);
  return $twig->render($template, $data);
}

// Routes
$app->get('/health', function(Request $req, Response $res) use ($serviceName) {
  $res->getBody()->write(json_encode(['status'=>'ok','service'=>$serviceName,'time'=>gmdate('c')]));
  return $res->withHeader('Content-Type','application/json');
});

$app->get('/admin/reset', function(Request $req, Response $res) use ($db) {
  $db->exec("DELETE FROM cart_items; DELETE FROM carts; DELETE FROM orders;");
  $res->getBody()->write(json_encode(['ok'=>true]));
  return $res->withHeader('Content-Type','application/json');
});

// Login routes
$app->get('/login', function(Request $req, Response $res) use ($twig) {
  if (Auth::isLoggedIn()) {
    return $res->withHeader('Location', '/products')->withStatus(302);
  }
  $res->getBody()->write(renderTwig($twig, 'login.twig'));
  return $res->withHeader('Content-Type', 'text/html');
});

$app->post('/login', function(Request $req, Response $res) use ($db, $twig, $log) {
  $body = $req->getParsedBody();
  $username = $body['username'] ?? '';
  $password = $body['password'] ?? '';

  $user = Db::findUser($db, $username);
  if ($user && password_verify($password, $user['password_hash'])) {
    Auth::login($user['id'], $user['username']);
    $log->info('login_success', ['username' => $username]);
    return $res->withHeader('Location', '/products')->withStatus(302);
  } else {
    $log->warning('login_failed', ['username' => $username]);
    $_SESSION['flash'] = ['type' => 'danger', 'message' => 'Invalid credentials'];
    return $res->withHeader('Location', '/login')->withStatus(302);
  }
});

$app->get('/logout', function(Request $req, Response $res) {
  Auth::logout();
  return $res->withHeader('Location', '/login')->withStatus(302);
});

// Protected routes
$app->get('/products', function(Request $req, Response $res) use ($db, $twig) {
  $q = $db->query("SELECT id,name,price,stock FROM products ORDER BY id");
  $products = $q->fetchAll(PDO::FETCH_ASSOC);
  $res->getBody()->write(renderTwig($twig, 'products.twig', ['products' => $products]));
  return $res->withHeader('Content-Type', 'text/html');
})->add($authMiddleware);

$app->post('/cart', function(Request $req, Response $res) use ($db) {
  $userId = Auth::getUserId();
  $cartId = "user_{$userId}";
  $body = (array)$req->getParsedBody();
  $pid = (int)($body['product_id'] ?? 0);
  $qty = (int)($body['qty'] ?? 0);
  if ($pid <= 0 || $qty < 0) {
    $res->getBody()->write(json_encode(['error'=>'VALIDATION_ERROR','details'=>'invalid product_id/qty']));
    return $res->withStatus(400)->withHeader('Content-Type','application/json');
  }
  $db->prepare("INSERT OR IGNORE INTO carts(id,created_at) VALUES(?,?)")->execute([$cartId, gmdate('c')]);
  if ($qty == 0) {
    $db->prepare("DELETE FROM cart_items WHERE cart_id=? AND product_id=?")->execute([$cartId, $pid]);
  } else {
    $db->prepare("INSERT INTO cart_items(cart_id,product_id,qty) VALUES(?,?,?)
                  ON CONFLICT(cart_id,product_id) DO UPDATE SET qty = excluded.qty")
       ->execute([$cartId,$pid,$qty]);
  }

  $stmt = $db->prepare("SELECT ci.qty,p.price FROM cart_items ci JOIN products p ON p.id=ci.product_id WHERE ci.cart_id=?");
  $stmt->execute([$cartId]);
  $items = $stmt->fetchAll(PDO::FETCH_ASSOC);
  $totalQty=0; $totalAmt=0; foreach ($items as $i){ $totalQty+=$i['qty']; $totalAmt += $i['qty']*$i['price']; }

  $res->getBody()->write(json_encode([
    'cart_id'=>$cartId, 'item'=>['product_id'=>$pid,'qty'=>$qty],
    'totals'=>['items'=>$totalQty,'amount'=>$totalAmt]
  ]));
  return $res->withHeader('Content-Type','application/json');
})->add($authMiddleware);

$app->get('/cart', function(Request $req, Response $res) use ($db, $twig) {
  $userId = Auth::getUserId();
  $cartId = "user_{$userId}";
  $stmt = $db->prepare("SELECT ci.product_id,ci.qty,p.name,p.price FROM cart_items ci JOIN products p ON p.id=ci.product_id WHERE ci.cart_id=?");
  $stmt->execute([$cartId]);
  $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

  $totalQty=0; $totalAmt=0; foreach ($rows as $r){ $totalQty+=$r['qty']; $totalAmt += $r['qty']*$r['price']; }
  $cart = ['cart_id'=>$cartId,'items'=>$rows,'totals'=>['items'=>$totalQty,'amount'=>$totalAmt]];

  $res->getBody()->write(renderTwig($twig, 'cart.twig', ['cart' => $cart]));
  return $res->withHeader('Content-Type', 'text/html');
})->add($authMiddleware);

$app->get('/checkout', function(Request $req, Response $res) use ($db, $twig) {
  $userId = Auth::getUserId();
  $cartId = "user_{$userId}";
  $stmt = $db->prepare("SELECT ci.product_id,ci.qty,p.name,p.price FROM cart_items ci JOIN products p ON p.id=ci.product_id WHERE ci.cart_id=?");
  $stmt->execute([$cartId]);
  $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
  if (!$rows) { return $res->withHeader('Location', '/cart')->withStatus(302); }
  $totalAmt=0; foreach ($rows as $r){ $totalAmt += $r['qty']*$r['price']; }
  $cart = ['cart_id'=>$cartId,'items'=>$rows,'totals'=>['amount'=>$totalAmt]];

  $res->getBody()->write(renderTwig($twig, 'checkout.twig', ['cart' => $cart]));
  return $res->withHeader('Content-Type', 'text/html');
})->add($authMiddleware);

$app->post('/checkout', function(Request $req, Response $res) use ($db, $env, $twig, $log) {
  $userId = Auth::getUserId();
  $cartId = "user_{$userId}";
  $stmt = $db->prepare("SELECT ci.qty,p.price FROM cart_items ci JOIN products p ON p.id=ci.product_id WHERE ci.cart_id=?");
  $stmt->execute([$cartId]);
  $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
  if (!$rows) { $_SESSION['flash'] = ['type' => 'danger', 'message' => 'Cart is empty']; return $res->withHeader('Location', '/cart')->withStatus(302); }
  $totalAmt=0; foreach ($rows as $r){ $totalAmt += $r['qty']*$r['price']; }

  $db->prepare("INSERT INTO orders(user_id,cart_id,total_amount,status,created_at) VALUES(?,?,?,?,?)")->execute([$userId, $cartId,$totalAmt,'PENDING',gmdate('c')]);
  $orderId = (int)$db->lastInsertId();

  $client = new \GuzzleHttp\Client(['base_uri'=>$env['PAYMENT_BASE_URL'],'timeout'=>5.0]);
  $body = $req->getParsedBody() ?: [];
  $cardLast4 = (string)($body['card_last4'] ?? '4242');

  $headers = [];
  foreach (['X-Chaos-Latency','X-Chaos-Error-Rate','X-Chaos-Force-Error','X-Chaos-Reject'] as $h) {
    $v = $req->getHeaderLine($h);
    if ($v !== '') $headers[$h] = $v;
  }

  try {
    $resp = $client->post('/pay', [
      'headers' => array_merge(['Content-Type'=>'application/json'], $headers),
      'json'    => ['order_id'=>$orderId,'amount'=>$totalAmt,'card_last4'=>$cardLast4],
    ]);
    $payment = json_decode((string)$resp->getBody(), true);
    if (($payment['status'] ?? '') === 'APPROVED') {
      $db->prepare("UPDATE orders SET status='PAID' WHERE id=?")->execute([$orderId]);
      // Update stock
      foreach ($rows as $item) {
        $db->prepare("UPDATE products SET stock = stock - ? WHERE id = ?")
           ->execute([$item['qty'], $item['product_id']]);
      }
      $log->info('checkout_success', ['order_id' => $orderId, 'total' => $totalAmt]);
      $order = ['order_id'=>$orderId,'status'=>'PAID','total_amount'=>$totalAmt,'created_at'=>gmdate('c')];
      $res->getBody()->write(renderTwig($twig, 'order.twig', ['order' => $order]));
      return $res->withHeader('Content-Type', 'text/html');
    } else {
      $db->prepare("UPDATE orders SET status='DECLINED' WHERE id=?")->execute([$orderId]);
      $_SESSION['flash'] = ['type' => 'danger', 'message' => 'Payment declined'];
      return $res->withHeader('Location', '/checkout')->withStatus(302);
    }
  } catch (\Throwable $e) {
    $db->prepare("UPDATE orders SET status='ERROR' WHERE id=?")->execute([$orderId]);
    $log->error('checkout_error', ['order_id' => $orderId, 'error' => $e->getMessage()]);
    $_SESSION['flash'] = ['type' => 'danger', 'message' => 'Payment failed'];
    return $res->withHeader('Location', '/checkout')->withStatus(302);
  }
})->add($authMiddleware);

$app->get('/orders/{id}', function(Request $req, Response $res, array $args) use ($db, $twig) {
  $id = (int)$args['id'];
  $stmt = $db->prepare("SELECT id as order_id, status, total_amount, created_at FROM orders WHERE id=? AND user_id=?");
  $stmt->execute([$id, Auth::getUserId()]);
  $row = $stmt->fetch(PDO::FETCH_ASSOC);
  if (!$row) return $res->withStatus(404)->getBody()->write('Order not found');
  $res->getBody()->write(renderTwig($twig, 'order.twig', ['order' => $row]));
  return $res->withHeader('Content-Type','text/html');
})->add($authMiddleware);

// Redirect root to login or products
$app->get('/', function(Request $req, Response $res) {
  $location = Auth::isLoggedIn() ? '/products' : '/login';
  return $res->withHeader('Location', $location)->withStatus(302);
});

$app->run();
