<?php
declare(strict_types=1);

namespace App\models;

use PDO;

class UserModel
{
    public function __construct(private PDO $db)
    {
    }

    public function findByUsername(string $username): ?array
    {
        $stmt = $this->db->prepare('SELECT id, username, password_hash, created_at FROM users WHERE username = :u LIMIT 1');
        $stmt->execute([':u' => $username]);
        $row = $stmt->fetch();
        return $row ?: null;
    }

    public function create(string $username, string $passwordHash): int
    {
        $stmt = $this->db->prepare('INSERT INTO users (username, password_hash, created_at) VALUES (:u, :p, :c)');
        $stmt->execute([
            ':u' => $username,
            ':p' => $passwordHash,
            ':c' => (new \DateTimeImmutable())->format('Y-m-d H:i:s'),
        ]);
        return (int)$this->db->lastInsertId();
    }
}
