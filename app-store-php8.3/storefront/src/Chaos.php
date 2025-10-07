<?php
namespace App;
final class Chaos {
  private int $defaultLatencyMs;
  private float $defaultErrorRate;
  public function __construct(int $latencyMs, float $errorRate) {
    $this->defaultLatencyMs = $latencyMs;
    $this->defaultErrorRate = $errorRate;
  }
  public function maybeSleep(?string $header): void {
    $ms = $header !== '' ? (int)$header : $this->defaultLatencyMs;
    if ($ms > 0) usleep($ms * 1000);
  }
  public function maybeError(?string $rateHeader, ?string $forceHeader): void {
    if (strtolower((string)$forceHeader) === 'true') throw new \RuntimeException("forced chaos error");
    $rate = $rateHeader !== '' ? (float)$rateHeader : $this->defaultErrorRate;
    if ($rate > 0 && mt_rand() / mt_getrandmax() < $rate) throw new \RuntimeException("random chaos error");
  }
}
