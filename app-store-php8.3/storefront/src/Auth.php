<?php
namespace App;
final class Auth {
  public static function startSession(): void {
    if (session_status() === PHP_SESSION_NONE) {
      session_start();
    }
  }

  public static function login(int $userId, string $username): void {
    self::startSession();
    session_regenerate_id(true);
    $_SESSION['user_id'] = $userId;
    $_SESSION['username'] = $username;
  }

  public static function logout(): void {
    self::startSession();
    session_destroy();
  }

  public static function isLoggedIn(): bool {
    self::startSession();
    return isset($_SESSION['user_id']);
  }

  public static function getUserId(): ?int {
    self::startSession();
    return $_SESSION['user_id'] ?? null;
  }

  public static function getUsername(): ?string {
    self::startSession();
    return $_SESSION['username'] ?? null;
  }

  public static function requireLogin(): void {
    if (!self::isLoggedIn()) {
      header('Location: /login');
      exit;
    }
  }
}
