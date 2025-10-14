<?php
declare(strict_types=1);

namespace App\models;

use PDO;
use PDOException;

class OrderModel
{
    public function __construct(private PDO $db)
    {
    }

    public function createOrder(int $userId, array $cart): int
    {
        if (empty($cart)) {
            throw new \InvalidArgumentException('Cart is empty');
        }

        $this->db->beginTransaction();
        try {
            $total = 0.0;
            foreach ($cart as $line) {
                $total += (float)$line['price'] * (int)$line['qty'];
            }

            $stmt = $this->db->prepare('INSERT INTO orders (user_id, order_date, total_amount) VALUES (:u, :d, :t)');
            $stmt->execute([
                ':u' => $userId,
                ':d' => (new \DateTimeImmutable())->format('Y-m-d H:i:s'),
                ':t' => $total,
            ]);
            $orderId = (int)$this->db->lastInsertId();

            $oi = new OrderItemModel($this->db);
            foreach ($cart as $line) {
                $oi->create($orderId, (int)$line['id'], (int)$line['qty'], (float)$line['price']);
            }

            $this->db->commit();
            return $orderId;
        } catch (PDOException $e) {
            $this->db->rollBack();
            throw $e;
        }
    }

    public function getOrdersWithItemsByUser(int $userId): array
    {
        $stmt = $this->db->prepare('SELECT id, user_id, order_date, total_amount FROM orders WHERE user_id = :u ORDER BY id DESC');
        $stmt->execute([':u' => $userId]);
        $orders = $stmt->fetchAll() ?: [];

        if (!$orders) {
            return [];
        }

        $ids = array_column($orders, 'id');
        $in = implode(',', array_fill(0, count($ids), '?'));

        $sql = "SELECT oi.id, oi.order_id, oi.product_id, oi.quantity, oi.unit_price,
                       p.name AS product_name
                FROM order_items oi
                JOIN products p ON p.id = oi.product_id
                WHERE oi.order_id IN ($in)
                ORDER BY oi.order_id ASC, oi.id ASC";

        $stmt = $this->db->prepare($sql);
        $stmt->execute($ids);
        $items = $stmt->fetchAll() ?: [];

        $byOrder = [];
        foreach ($items as $it) {
            $byOrder[(int)$it['order_id']][] = $it;
        }

        foreach ($orders as &$o) {
            $o['items'] = $byOrder[(int)$o['id']] ?? [];
        }
        unset($o);

        return $orders;
    }
}
