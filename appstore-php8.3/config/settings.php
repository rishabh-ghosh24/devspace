<?php
declare(strict_types=1);

return function (): array {
    return [
        'displayErrorDetails' => false, // set true for local dev if needed
        'log' => [
            'path' => dirname(__DIR__) . '/logs/app.log',
            'level' => 'INFO',
        ],
        'db' => [
            'driver' => 'sqlite',
            'database' => dirname(__DIR__) . '/database/appstore.db',
        ],
        'app' => [
            'base_url' => '/', // used for links if needed
            'session_name' => 'appstore_sess',
        ],
    ];
};
