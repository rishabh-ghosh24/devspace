<?php
declare(strict_types=1);

namespace App\models;

use PDO;

class ProductModel
{
    public function __construct(private PDO $db)
    {
    }

    public function all(): array
    {
        $stmt = $this->db->query('SELECT id, name, description, price, image_url, created_at FROM products ORDER BY id ASC');
        return $stmt->fetchAll() ?: [];
    }

    public function find(int $id): ?array
    {
        $stmt = $this->db->prepare('SELECT id, name, description, price, image_url, created_at FROM products WHERE id = :id');
        $stmt->execute([':id' => $id]);
        $row = $stmt->fetch();
        return $row ?: null;
    }
}
