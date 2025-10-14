<?php
declare(strict_types=1);

use Monolog\Level;
use Monolog\Logger;
use Monolog\Handler\StreamHandler;
use Monolog\Processor\UidProcessor;

return function (array $settings): Logger {
    $logPath = $settings['log']['path'] ?? (dirname(__DIR__) . '/logs/app.log');
    $levelStr = strtoupper((string)($settings['log']['level'] ?? 'INFO'));

    $level = match ($levelStr) {
        'DEBUG' => Level::Debug,
        'INFO' => Level::Info,
        'NOTICE' => Level::Notice,
        'WARNING' => Level::Warning,
        'ERROR' => Level::Error,
        'CRITICAL' => Level::Critical,
        'ALERT' => Level::Alert,
        'EMERGENCY' => Level::Emergency,
        default => Level::Info,
    };

    // Ensure directory exists
    $dir = dirname($logPath);
    if (!is_dir($dir)) {
        @mkdir($dir, 0775, true);
    }

    $logger = new Logger('appstore');
    $logger->pushProcessor(new UidProcessor());
    $logger->pushHandler(new StreamHandler($logPath, $level));

    return $logger;
};
