<?php
namespace Pay;
use Monolog\Logger;
use Monolog\Handler\StreamHandler;
use Monolog\Formatter\JsonFormatter;
use Monolog\LogRecord;

final class Log {
  public static function create(string $service, string $path): Logger {
    $log = new Logger($service);
    $h = new StreamHandler($path, Logger::DEBUG, true, 0644);
    $h->setFormatter(new JsonFormatter());
    $log->pushHandler($h);
    $log->pushProcessor(function(LogRecord $record) use ($service){
      $record['extra']['service'] = $service;
      $record['extra']['timestamp'] = gmdate('c');
      if (function_exists('opentelemetry_get_trace_id')) {
        $record['extra']['trace_id'] = opentelemetry_get_trace_id() ?: null;
        $record['extra']['span_id']  = function_exists('opentelemetry_get_span_id') ? opentelemetry_get_span_id() : null;
      }
      return $record;
    });
    return $log;
  }
}
