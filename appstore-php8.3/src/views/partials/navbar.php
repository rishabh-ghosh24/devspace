<?php
declare(strict_types=1);
/** @var bool $isAuthenticated */
/** @var ?string $username */
?>
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <div class="container">
    <a class="navbar-brand" href="/products">AppStore</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarsExampleDefault" aria-controls="navbarsExampleDefault" aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>

    <div class="collapse navbar-collapse" id="navbarsExampleDefault">
      <ul class="navbar-nav me-auto mb-2 mb-lg-0">
        <li class="nav-item"><a class="nav-link" href="/products">Products</a></li>
        <li class="nav-item"><a class="nav-link" href="/cart">Cart</a></li>
        <?php if ($isAuthenticated ?? false): ?>
          <li class="nav-item"><a class="nav-link" href="/orders">Orders</a></li>
        <?php endif; ?>
        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
            Simulate
          </a>
          <ul class="dropdown-menu">
            <li><a class="dropdown-item" href="/simulate/slow">Slow (3–5s)</a></li>
            <li><a class="dropdown-item" href="/simulate/error">Error (500)</a></li>
          </ul>
        </li>
      </ul>

      <ul class="navbar-nav ms-auto mb-2 mb-lg-0">
        <?php if ($isAuthenticated ?? false): ?>
          <li class="nav-item">
            <span class="navbar-text me-3">Hello, <?= htmlspecialchars((string)$username) ?></span>
          </li>
          <li class="nav-item"><a class="btn btn-outline-light btn-sm" href="/logout">Logout</a></li>
        <?php else: ?>
          <li class="nav-item"><a class="btn btn-outline-light btn-sm" href="/login">Login</a></li>
        <?php endif; ?>
      </ul>
    </div>
  </div>
</nav>
