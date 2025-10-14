<?php
declare(strict_types=1);
/** @var string $title */
/** @var ?array $product */
/** @var bool $isAuthenticated */
/** @var ?string $username */
$this->layout('layout', [
  'title' => $title ?? 'Product',
  'isAuthenticated' => $isAuthenticated ?? false,
  'username' => $username ?? null,
]);
?>
<?php $this->start('body') ?>
<?php if (!$product): ?>
  <div class="alert alert-warning">Product not found.</div>
  <a href="/products" class="btn btn-secondary">Back to Products</a>
<?php else: ?>
  <div class="row">
    <div class="col-md-6">
      <img src="<?= htmlspecialchars((string)$product['image_url']) ?>" alt="<?= htmlspecialchars((string)$product['name']) ?>" class="img-fluid rounded shadow-sm">
    </div>
    <div class="col-md-6">
      <h1 class="h3"><?= htmlspecialchars((string)$product['name']) ?></h1>
      <p class="text-muted">$<?= number_format((float)$product['price'], 2) ?></p>
      <p><?= nl2br(htmlspecialchars((string)$product['description'])) ?></p>

      <form method="post" action="/cart/add" class="row gy-2 gx-2 align-items-center">
        <input type="hidden" name="product_id" value="<?= (int)$product['id'] ?>">
        <div class="col-auto">
          <label for="qty" class="col-form-label">Qty</label>
        </div>
        <div class="col-auto">
          <input id="qty" name="qty" type="number" min="1" value="1" class="form-control" style="width:100px">
        </div>
        <div class="col-auto">
          <button class="btn btn-primary" type="submit">Add to Cart</button>
        </div>
      </form>
      <div class="mt-3">
        <a href="/products" class="btn btn-outline-secondary">Back to Products</a>
      </div>
    </div>
  </div>
<?php endif; ?>
<?php $this->end() ?>
