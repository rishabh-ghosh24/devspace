<?php
declare(strict_types=1);
/** @var string $title */
/** @var ?string $error */
/** @var array $old */
$this->layout('layout', [
  'title' => $title ?? 'Login',
  'isAuthenticated' => false,
  'username' => null,
]);
?>
<?php $this->start('body') ?>
<div class="row justify-content-center">
  <div class="col-md-5">
    <div class="card shadow-sm">
      <div class="card-body">
        <h1 class="h4 mb-3">Sign in</h1>
        <?php if (!empty($error)): ?>
          <div class="alert alert-danger"><?= htmlspecialchars((string)$error) ?></div>
        <?php endif; ?>
        <form method="post" action="/login" autocomplete="off" novalidate>
          <div class="mb-3">
            <label for="username" class="form-label">Username</label>
            <input id="username" name="username" type="text" class="form-control" required value="<?= htmlspecialchars((string)($old['username'] ?? '')) ?>">
          </div>
          <div class="mb-3">
            <label for="password" class="form-label">Password</label>
            <input id="password" name="password" type="password" class="form-control" required>
          </div>
          <button class="btn btn-primary" type="submit">Login</button>
        </form>
        <hr>
        <p class="text-muted small mb-0">Demo credentials: admin / demo123</p>
      </div>
    </div>
  </div>
</div>
<?php $this->end() ?>
