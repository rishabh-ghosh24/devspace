<?php
declare(strict_types=1);
/** @var string $title */
/** @var array $products */
/** @var bool $isAuthenticated */
/** @var ?string $username */
$this->layout('layout', [
  'title' => $title ?? 'Products',
  'isAuthenticated' => $isAuthenticated ?? false,
  'username' => $username ?? null,
]);
?>
<?php $this->start('body') ?>
<h1 class="h3 mb-4">Products</h1>

<?php if (empty($products)): ?>
  <div class="alert alert-info">No products available.</div>
<?php else: ?>
  <div class="row row-cols-1 row-cols-sm-2 row-cols-md-3 g-4">
    <?php foreach ($products as $p): ?>
      <div class="col">
        <div class="card h-100">
          <img src="<?= htmlspecialchars((string)$p['image_url']) ?>" class="card-img-top" alt="<?= htmlspecialchars((string)$p['name']) ?>">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title"><?= htmlspecialchars((string)$p['name']) ?></h5>
            <p class="card-text text-muted mb-2">$<?= number_format((float)$p['price'], 2) ?></p>
            <div class="mt-auto d-flex gap-2">
              <a class="btn btn-outline-secondary btn-sm" href="/product/<?= (int)$p['id'] ?>">View</a>
              <form method="post" action="/cart/add" class="d-inline">
                <input type="hidden" name="product_id" value="<?= (int)$p['id'] ?>">
                <input type="hidden" name="qty" value="1">
                <button class="btn btn-primary btn-sm" type="submit">Add to Cart</button>
              </form>
            </div>
          </div>
        </div>
      </div>
    <?php endforeach; ?>
  </div>
<?php endif; ?>
<?php $this->end() ?>
