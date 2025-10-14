<?php
declare(strict_types=1);

namespace App\models;

use PDO;

class OrderItemModel
{
    public function __construct(private PDO $db)
    {
    }

    public function create(int $orderId, int $productId, int $qty, float $unitPrice): int
    {
        $stmt = $this->db->prepare(
            'INSERT INTO order_items (order_id, product_id, quantity, unit_price) 
             VALUES (:o, :p, :q, :u)'
        );
        $stmt->execute([
            ':o' => $orderId,
            ':p' => $productId,
            ':q' => $qty,
            ':u' => $unitPrice,
        ]);
        return (int)$this->db->lastInsertId();
    }
}
