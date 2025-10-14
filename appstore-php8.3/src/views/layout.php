<?php
declare(strict_types=1);
/** @var string $title */
/** @var bool $isAuthenticated */
/** @var ?string $username */
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title><?= $this->e($title ?? 'AppStore') ?></title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" crossorigin="anonymous">
</head>
<body>
  <header>
    <?= $this->insert('partials/navbar', [
        'isAuthenticated' => $isAuthenticated ?? false,
        'username' => $username ?? null,
    ]) ?>
  </header>
  <main class="container py-4">
    <?= $this->section('body') ?>
  </main>
  <footer class="border-top py-3 mt-4">
    <div class="container text-muted small">
      AppStore PHP 8.3 — Phase 1 (MVP)
    </div>
  </footer>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" crossorigin="anonymous"></script>
</body>
</html>
