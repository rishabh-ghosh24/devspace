<?php
namespace App;
use PDO;
final class Db {
  public static function connect(string $path): PDO {
    $pdo = new PDO('sqlite:' . $path, null, null, [
      PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
      PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);
    return $pdo;
  }
  public static function migrateStorefront(PDO $db): void {
    $db->exec("CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      created_at TEXT NOT NULL)");
    $db->exec("CREATE TABLE IF NOT EXISTS products(
      id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, price INTEGER NOT NULL, stock INTEGER NOT NULL)");
    $db->exec("CREATE TABLE IF NOT EXISTS carts(
      id TEXT PRIMARY KEY, created_at TEXT NOT NULL)");
    $db->exec("CREATE TABLE IF NOT EXISTS cart_items(
      cart_id TEXT NOT NULL, product_id INTEGER NOT NULL, qty INTEGER NOT NULL,
      PRIMARY KEY(cart_id, product_id))");
    $db->exec("CREATE TABLE IF NOT EXISTS orders(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, cart_id TEXT NOT NULL,
      total_amount INTEGER NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id))");

    // Seed admin user if not exists
    $stmt = $db->prepare("SELECT COUNT(*) as count FROM users WHERE username = ?");
    $stmt->execute(['admin']);
    if ($stmt->fetch()['count'] == 0) {
      $hash = password_hash('securePass123', PASSWORD_DEFAULT);
      $db->prepare("INSERT INTO users(username, password_hash, created_at) VALUES(?,?,?)")
         ->execute(['admin', $hash, gmdate('c')]);
    }

    // Seed products
    $stmt = $db->prepare("SELECT COUNT(*) as count FROM products");
    $stmt->execute();
    if ($stmt->fetch()['count'] == 0) {
      $products = [['Widget', 1999, 24], ['Gadget', 2999, 15], ['Doodad', 999, 100]];
      $stmt = $db->prepare("INSERT INTO products(name, price, stock) VALUES (?,?,?)");
      foreach ($products as $p) { $stmt->execute($p); }
    }
  }

  public static function findUser(PDO $db, string $username): ?array {
    $stmt = $db->prepare("SELECT id, username, password_hash FROM users WHERE username = ?");
    $stmt->execute([$username]);
    return $stmt->fetch() ?: null;
  }
}
