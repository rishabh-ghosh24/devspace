"""Configuration dataclasses for OCI Log Analytics MCP Server."""

from dataclasses import dataclass, field
from typing import Optional, Literal
from pathlib import Path


@dataclass
class OCIConfig:
    """OCI authentication configuration."""

    config_path: Path = field(default_factory=lambda: Path.home() / ".oci" / "config")
    profile: str = "DEFAULT"
    auth_type: Literal["config_file", "instance_principal", "resource_principal"] = "config_file"


@dataclass
class LogAnalyticsConfig:
    """Log Analytics service configuration."""

    namespace: str = ""
    default_compartment_id: str = ""
    default_log_group_id: Optional[str] = None


@dataclass
class QueryConfig:
    """Query execution configuration."""

    default_time_range: str = "last_1_hour"
    max_results: int = 1000
    timeout_seconds: int = 60


@dataclass
class CacheConfig:
    """Caching configuration."""

    enabled: bool = True
    query_ttl_minutes: int = 5
    schema_ttl_minutes: int = 15


@dataclass
class LoggingConfig:
    """Logging configuration."""

    query_logging: bool = True
    log_path: Path = field(default_factory=lambda: Path.home() / ".oci-la-mcp" / "logs")
    log_level: str = "INFO"


@dataclass
class GuardrailsConfig:
    """Query guardrails configuration."""

    max_time_range_days: int = 7
    warn_on_large_results: bool = True
    large_result_threshold: int = 10000


@dataclass
class Settings:
    """Main settings container."""

    oci: OCIConfig = field(default_factory=OCIConfig)
    log_analytics: LogAnalyticsConfig = field(default_factory=LogAnalyticsConfig)
    query: QueryConfig = field(default_factory=QueryConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    guardrails: GuardrailsConfig = field(default_factory=GuardrailsConfig)

    def to_dict(self) -> dict:
        """Convert settings to dictionary for serialization."""
        return {
            "oci": {
                "config_path": str(self.oci.config_path),
                "profile": self.oci.profile,
                "auth_type": self.oci.auth_type,
            },
            "log_analytics": {
                "namespace": self.log_analytics.namespace,
                "default_compartment_id": self.log_analytics.default_compartment_id,
                "default_log_group_id": self.log_analytics.default_log_group_id,
            },
            "query": {
                "default_time_range": self.query.default_time_range,
                "max_results": self.query.max_results,
                "timeout_seconds": self.query.timeout_seconds,
            },
            "cache": {
                "enabled": self.cache.enabled,
                "query_ttl_minutes": self.cache.query_ttl_minutes,
                "schema_ttl_minutes": self.cache.schema_ttl_minutes,
            },
            "logging": {
                "query_logging": self.logging.query_logging,
                "log_path": str(self.logging.log_path),
                "log_level": self.logging.log_level,
            },
            "guardrails": {
                "max_time_range_days": self.guardrails.max_time_range_days,
                "warn_on_large_results": self.guardrails.warn_on_large_results,
                "large_result_threshold": self.guardrails.large_result_threshold,
            },
        }
