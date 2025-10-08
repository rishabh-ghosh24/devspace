<?php
namespace App;
use Monolog\Logger;
use Monolog\Handler\StreamHandler;
use Monolog\Formatter\JsonFormatter;

final class Log {
  public static function create(string $service, string $path): Logger {
    $log = new Logger($service);
    $h = new StreamHandler($path, Logger::DEBUG, true, 0644);
    $h->setFormatter(new JsonFormatter());
    $log->pushHandler($h);
    $log->pushProcessor(function(array $record) use ($service){
      $record['extra']['service'] = $service;
      $record['extra']['timestamp'] = gmdate('c');
      $record['extra']['user_id'] = \App\Auth::getUserId();
      // Workaround for trace context without PECL extension
      if (isset($_SERVER['HTTP_TRACEPARENT'])) {
        $parts = explode('-', $_SERVER['HTTP_TRACEPARENT']);
        $record['extra']['trace_id'] = $parts[1] ?? null;
        $record['extra']['span_id'] = $parts[2] ?? null;
      } elseif (function_exists('opentelemetry_get_trace_id')) {
        $record['extra']['trace_id'] = opentelemetry_get_trace_id() ?: null;
        $record['extra']['span_id']  = function_exists('opentelemetry_get_span_id') ? opentelemetry_get_span_id() : null;
      }
      return $record;
    });
    return $log;
  }
}
