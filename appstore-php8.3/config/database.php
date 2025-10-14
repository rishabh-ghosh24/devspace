<?php
declare(strict_types=1);

use Monolog\Logger;

return function (array $settings, Logger $logger): PDO {
    $dbConf = $settings['db'] ?? [];
    $driver = $dbConf['driver'] ?? 'sqlite';

    if ($driver !== 'sqlite') {
        throw new RuntimeException('Only SQLite is supported in Phase 1.');
    }

    $dbPath = $dbConf['database'] ?? (dirname(__DIR__) . '/database/appstore.db');

    // Ensure directory exists
    $dir = dirname($dbPath);
    if (!is_dir($dir)) {
        @mkdir($dir, 0775, true);
    }

    $dsn = "sqlite:" . $dbPath;

    try {
        $pdo = new PDO($dsn, null, null, [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
        ]);
        // Enforce foreign keys
        $pdo->exec('PRAGMA foreign_keys = ON;');

        $logger->info('SQLite connection established', ['path' => $dbPath]);

        return $pdo;
    } catch (PDOException $e) {
        $logger->error('Database connection failed', ['error' => $e->getMessage()]);
        throw $e;
    }
};
