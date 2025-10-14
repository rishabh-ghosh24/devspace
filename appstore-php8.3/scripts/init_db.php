<?php
declare(strict_types=1);

// Bootstrap minimal autoload and config to get PDO
require __DIR__ . '/../vendor/autoload.php';

define('ROOT_DIR', dirname(__DIR__));

// Settings
$settingsFactory = require ROOT_DIR . '/config/settings.php';
$settings = $settingsFactory();

// Logger (optional during init)
$loggerFactory = require ROOT_DIR . '/config/logger.php';
$logger = $loggerFactory($settings);

// DB
$dbFactory = require ROOT_DIR . '/config/database.php';
$pdo = $dbFactory($settings, $logger);

// Schema creation
$pdo->exec('
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at DATETIME NOT NULL
);
');

$pdo->exec('
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  price REAL NOT NULL,
  image_url TEXT NOT NULL,
  created_at DATETIME NOT NULL
);
');

$pdo->exec('
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  order_date DATETIME NOT NULL,
  total_amount REAL NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
');

$pdo->exec('
CREATE TABLE IF NOT EXISTS order_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  unit_price REAL NOT NULL,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);
');

// Seed demo user if not exists
$exists = $pdo->prepare('SELECT COUNT(*) AS c FROM users WHERE username = :u');
$exists->execute([':u' => 'admin']);
$count = (int)$exists->fetchColumn();
if ($count === 0) {
    $hash = password_hash('demo123', PASSWORD_BCRYPT);
    $stmt = $pdo->prepare('INSERT INTO users (username, password_hash, created_at) VALUES (:u, :p, :c)');
    $stmt->execute([
        ':u' => 'admin',
        ':p' => $hash,
        ':c' => (new DateTimeImmutable())->format('Y-m-d H:i:s'),
    ]);
    $logger->info('Seeded demo user "admin"');
} else {
    $logger->info('Demo user already exists, skipping.');
}

// Seed products if table empty
$prodCount = (int)$pdo->query('SELECT COUNT(*) FROM products')->fetchColumn();
if ($prodCount === 0) {
    $now = (new DateTimeImmutable())->format('Y-m-d H:i:s');
    $products = [
        ['Wireless Headphones', 'High-fidelity wireless headphones with noise cancellation and 30h battery life.', 129.99, 'https://picsum.photos/seed/headphones/600/400'],
        ['Smart Watch', 'Water-resistant smart watch with heart-rate monitoring and GPS.', 179.00, 'https://picsum.photos/seed/smartwatch/600/400'],
        ['Bluetooth Speaker', 'Portable Bluetooth speaker with deep bass and 12h playtime.', 59.50, 'https://picsum.photos/seed/speaker/600/400'],
        ['4K Action Camera', 'Compact 4K action camera with stabilization and waterproof case.', 229.99, 'https://picsum.photos/seed/camera/600/400'],
        ['USB-C Hub', '7-in-1 USB-C hub with HDMI, USB 3.0, SD/TF, and PD charging.', 39.00, 'https://picsum.photos/seed/hub/600/400'],
        ['Mechanical Keyboard', 'RGB mechanical keyboard with tactile switches and detachable cable.', 89.00, 'https://picsum.photos/seed/keyboard/600/400'],
        ['Gaming Mouse', 'Ergonomic gaming mouse with adjustable DPI and programmable buttons.', 34.99, 'https://picsum.photos/seed/mouse/600/400'],
        ['27" 144Hz Monitor', '27-inch IPS monitor with 144Hz refresh rate and low input lag.', 299.00, 'https://picsum.photos/seed/monitor/600/400'],
        ['External SSD 1TB', 'Portable 1TB NVMe SSD with USB 3.2 Gen 2 speeds.', 119.00, 'https://picsum.photos/seed/ssd/600/400'],
        ['Webcam 1080p', 'Full HD 1080p webcam with dual microphones and privacy shutter.', 49.99, 'https://picsum.photos/seed/webcam/600/400'],
    ];
    $stmt = $pdo->prepare('INSERT INTO products (name, description, price, image_url, created_at) VALUES (:n, :d, :p, :i, :c)');
    foreach ($products as [$name, $desc, $price, $img]) {
        $stmt->execute([
            ':n' => $name,
            ':d' => $desc,
            ':p' => $price,
            ':i' => $img,
            ':c' => $now,
        ]);
    }
    $logger->info('Seeded products', ['count' => count($products)]);
} else {
    $logger->info('Products already exist, skipping seed.', ['count' => $prodCount]);
}

echo "Database initialized successfully.\n";
