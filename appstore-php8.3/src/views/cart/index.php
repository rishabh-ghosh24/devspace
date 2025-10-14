<?php
declare(strict_types=1);
/** @var string $title */
/** @var array $cart */
/** @var float $total */
/** @var bool $isAuthenticated */
/** @var ?string $username */
$this->layout('layout', [
  'title' => $title ?? 'Your Cart',
  'isAuthenticated' => $isAuthenticated ?? false,
  'username' => $username ?? null,
]);
?>
<?php $this->start('body') ?>
<h1 class="h3 mb-4">Your Cart</h1>

<?php if (empty($cart)): ?>
  <div class="alert alert-info">Your cart is empty.</div>
  <a href="/products" class="btn btn-primary">Browse Products</a>
<?php else: ?>
  <div class="table-responsive">
    <table class="table align-middle">
      <thead>
        <tr>
          <th>Product</th>
          <th style="width:120px;">Price</th>
          <th style="width:160px;">Quantity</th>
          <th style="width:140px;">Line Total</th>
          <th style="width:120px;">Actions</th>
        </tr>
      </thead>
      <tbody>
      <?php foreach ($cart as $line): ?>
        <tr>
          <td><?= htmlspecialchars((string)$line['name']) ?></td>
          <td>$<?= number_format((float)$line['price'], 2) ?></td>
          <td>
            <form class="d-flex gap-2" method="post" action="/cart/update">
              <input type="hidden" name="product_id" value="<?= (int)$line['id'] ?>">
              <input type="number" min="0" class="form-control form-control-sm" name="qty" value="<?= (int)$line['qty'] ?>" style="width: 80px;">
              <button class="btn btn-sm btn-outline-secondary" type="submit">Update</button>
            </form>
          </td>
          <td>$<?= number_format((float)$line['price'] * (int)$line['qty'], 2) ?></td>
          <td>
            <form method="post" action="/cart/remove">
              <input type="hidden" name="product_id" value="<?= (int)$line['id'] ?>">
              <button class="btn btn-sm btn-outline-danger" type="submit">Remove</button>
            </form>
          </td>
        </tr>
      <?php endforeach; ?>
      </tbody>
      <tfoot>
        <tr>
          <th colspan="3" class="text-end">Total:</th>
          <th>$<?= number_format($total, 2) ?></th>
          <th></th>
        </tr>
      </tfoot>
    </table>
  </div>

  <div class="d-flex justify-content-between">
    <a class="btn btn-outline-secondary" href="/products">Continue Shopping</a>
    <form method="post" action="/checkout">
      <button class="btn btn-success" type="submit">Proceed to Checkout</button>
    </form>
  </div>
<?php endif; ?>
<?php $this->end() ?>
