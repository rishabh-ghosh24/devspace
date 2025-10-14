<?php
declare(strict_types=1);
/** @var string $title */
/** @var array $orders */
/** @var bool $isAuthenticated */
/** @var ?string $username */
$this->layout('layout', [
  'title' => $title ?? 'Your Orders',
  'isAuthenticated' => $isAuthenticated ?? false,
  'username' => $username ?? null,
]);
?>
<?php $this->start('body') ?>
<h1 class="h3 mb-4">Your Orders</h1>

<?php if (empty($orders)): ?>
  <div class="alert alert-info">No orders yet.</div>
  <a href="/products" class="btn btn-primary">Browse Products</a>
<?php else: ?>
  <div class="accordion" id="ordersAccordion">
    <?php foreach ($orders as $idx => $o): ?>
      <?php
        $orderId = (int)$o['id'];
        $headingId = "heading{$orderId}";
        $collapseId = "collapse{$orderId}";
      ?>
      <div class="accordion-item">
        <h2 class="accordion-header" id="<?= $headingId ?>">
          <button class="accordion-button <?= $idx === 0 ? '' : 'collapsed' ?>" type="button" data-bs-toggle="collapse" data-bs-target="#<?= $collapseId ?>" aria-expanded="<?= $idx === 0 ? 'true' : 'false' ?>" aria-controls="<?= $collapseId ?>">
            Order #<?= $orderId ?> — <?= htmlspecialchars((string)$o['order_date']) ?> — Total: $<?= number_format((float)$o['total_amount'], 2) ?>
          </button>
        </h2>
        <div id="<?= $collapseId ?>" class="accordion-collapse collapse <?= $idx === 0 ? 'show' : '' ?>" aria-labelledby="<?= $headingId ?>" data-bs-parent="#ordersAccordion">
          <div class="accordion-body">
            <?php if (empty($o['items'])): ?>
              <div class="text-muted">No items recorded for this order.</div>
            <?php else: ?>
              <div class="table-responsive">
                <table class="table table-sm">
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>Unit Price</th>
                      <th>Qty</th>
                      <th>Line Total</th>
                    </tr>
                  </thead>
                  <tbody>
                  <?php foreach ($o['items'] as $it): ?>
                    <tr>
                      <td><?= htmlspecialchars((string)$it['product_name']) ?></td>
                      <td>$<?= number_format((float)$it['unit_price'], 2) ?></td>
                      <td><?= (int)$it['quantity'] ?></td>
                      <td>$<?= number_format((float)$it['unit_price'] * (int)$it['quantity'], 2) ?></td>
                    </tr>
                  <?php endforeach; ?>
                  </tbody>
                </table>
              </div>
            <?php endif; ?>
          </div>
        </div>
      </div>
    <?php endforeach; ?>
  </div>
<?php endif; ?>

<div class="mt-4">
  <a href="/products" class="btn btn-outline-secondary">Back to Products</a>
</div>
<?php $this->end() ?>
