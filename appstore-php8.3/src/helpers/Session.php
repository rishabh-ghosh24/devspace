<?php
declare(strict_types=1);

namespace App\helpers;

class Session
{
    public static function get(string $key, mixed $default = null): mixed
    {
        return $_SESSION[$key] ?? $default;
    }

    public static function set(string $key, mixed $value): void
    {
        $_SESSION[$key] = $value;
    }

    public static function remove(string $key): void
    {
        unset($_SESSION[$key]);
    }

    public static function regenerate(): void
    {
        if (session_status() === PHP_SESSION_ACTIVE) {
            session_regenerate_id(true);
        }
    }

    // Auth helpers
    public static function login(int $userId, string $username): void
    {
        self::set('user_id', $userId);
        self::set('username', $username);
        self::regenerate();
    }

    public static function logout(): void
    {
        $_SESSION = [];
        if (ini_get('session.use_cookies')) {
            $params = session_get_cookie_params();
            setcookie(session_name(), '', time() - 42000, $params['path'], $params['domain'], (bool)$params['secure'], (bool)$params['httponly']);
        }
        session_destroy();
    }

    public static function userId(): ?int
    {
        $id = self::get('user_id');
        return is_int($id) ? $id : (is_numeric($id) ? (int)$id : null);
    }

    public static function username(): ?string
    {
        $u = self::get('username');
        return is_string($u) ? $u : null;
    }

    public static function isAuthenticated(): bool
    {
        return self::userId() !== null;
    }

    // Cart helpers: cart is an associative array: product_id => ['id', 'name', 'price', 'qty']
    public static function getCart(): array
    {
        return self::get('cart', []);
    }

    public static function setCart(array $cart): void
    {
        self::set('cart', $cart);
    }

    public static function addToCart(int $productId, string $name, float $price, int $qty = 1): void
    {
        $cart = self::getCart();
        if (isset($cart[$productId])) {
            $cart[$productId]['qty'] += $qty;
        } else {
            $cart[$productId] = [
                'id' => $productId,
                'name' => $name,
                'price' => $price,
                'qty' => max(1, $qty),
            ];
        }
        self::setCart($cart);
    }

    public static function updateQty(int $productId, int $qty): void
    {
        $cart = self::getCart();
        if (isset($cart[$productId])) {
            if ($qty <= 0) {
                unset($cart[$productId]);
            } else {
                $cart[$productId]['qty'] = $qty;
            }
            self::setCart($cart);
        }
    }

    public static function removeFromCart(int $productId): void
    {
        $cart = self::getCart();
        if (isset($cart[$productId])) {
            unset($cart[$productId]);
            self::setCart($cart);
        }
    }

    public static function clearCart(): void
    {
        self::remove('cart');
    }
}
