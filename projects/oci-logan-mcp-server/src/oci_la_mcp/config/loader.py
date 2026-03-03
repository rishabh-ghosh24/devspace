"""Configuration file and environment variable loading."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .settings import (
    Settings,
    OCIConfig,
    LogAnalyticsConfig,
    QueryConfig,
    CacheConfig,
    LoggingConfig,
    GuardrailsConfig,
)

CONFIG_PATH = Path.home() / ".oci-la-mcp" / "config.yaml"


def load_config(config_path: Optional[Path] = None) -> Settings:
    """Load configuration from file, with environment variable overrides.

    Args:
        config_path: Optional path to config file. Uses default if not specified.

    Returns:
        Settings object with loaded configuration.
    """
    settings = Settings()

    # Check for config path override from environment
    if env_config_path := os.environ.get("OCI_LA_MCP_CONFIG"):
        config_path = Path(env_config_path)
    elif config_path is None:
        config_path = CONFIG_PATH

    # Load from file if exists
    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
            settings = _parse_config(data)

    # Apply environment variable overrides
    settings = _apply_env_overrides(settings)

    return settings


def _parse_config(data: Dict[str, Any]) -> Settings:
    """Parse configuration dictionary into Settings object.

    Args:
        data: Dictionary loaded from YAML config file.

    Returns:
        Settings object populated from the dictionary.
    """
    settings = Settings()

    # Parse OCI config
    if oci_data := data.get("oci"):
        settings.oci = OCIConfig(
            config_path=Path(oci_data.get("config_path", str(settings.oci.config_path))),
            profile=oci_data.get("profile", settings.oci.profile),
            auth_type=oci_data.get("auth_type", settings.oci.auth_type),
        )

    # Parse Log Analytics config
    if la_data := data.get("log_analytics"):
        settings.log_analytics = LogAnalyticsConfig(
            namespace=la_data.get("namespace", settings.log_analytics.namespace),
            default_compartment_id=la_data.get(
                "default_compartment_id", settings.log_analytics.default_compartment_id
            ),
            default_log_group_id=la_data.get("default_log_group_id"),
        )

    # Parse Query config
    if query_data := data.get("query"):
        settings.query = QueryConfig(
            default_time_range=query_data.get(
                "default_time_range", settings.query.default_time_range
            ),
            max_results=query_data.get("max_results", settings.query.max_results),
            timeout_seconds=query_data.get("timeout_seconds", settings.query.timeout_seconds),
        )

    # Parse Cache config
    if cache_data := data.get("cache"):
        settings.cache = CacheConfig(
            enabled=cache_data.get("enabled", settings.cache.enabled),
            query_ttl_minutes=cache_data.get("query_ttl_minutes", settings.cache.query_ttl_minutes),
            schema_ttl_minutes=cache_data.get(
                "schema_ttl_minutes", settings.cache.schema_ttl_minutes
            ),
        )

    # Parse Logging config
    if logging_data := data.get("logging"):
        settings.logging = LoggingConfig(
            query_logging=logging_data.get("query_logging", settings.logging.query_logging),
            log_path=Path(logging_data.get("log_path", str(settings.logging.log_path))),
            log_level=logging_data.get("log_level", settings.logging.log_level),
        )

    # Parse Guardrails config
    if guardrails_data := data.get("guardrails"):
        settings.guardrails = GuardrailsConfig(
            max_time_range_days=guardrails_data.get(
                "max_time_range_days", settings.guardrails.max_time_range_days
            ),
            warn_on_large_results=guardrails_data.get(
                "warn_on_large_results", settings.guardrails.warn_on_large_results
            ),
            large_result_threshold=guardrails_data.get(
                "large_result_threshold", settings.guardrails.large_result_threshold
            ),
        )

    return settings


def _apply_env_overrides(settings: Settings) -> Settings:
    """Override settings with environment variables.

    Environment variables:
        OCI_LA_NAMESPACE: Log Analytics namespace
        OCI_LA_COMPARTMENT: Default compartment OCID
        OCI_CONFIG_PATH: Path to OCI config file
        OCI_CONFIG_PROFILE: OCI config profile name
        OCI_LA_AUTH_TYPE: Authentication type
        OCI_LA_TIMEOUT: Query timeout in seconds
        OCI_LA_LOG_LEVEL: Logging level

    Args:
        settings: Settings object to update.

    Returns:
        Updated Settings object.
    """
    env_mappings = {
        "OCI_LA_NAMESPACE": ("log_analytics", "namespace"),
        "OCI_LA_COMPARTMENT": ("log_analytics", "default_compartment_id"),
        "OCI_CONFIG_PATH": ("oci", "config_path"),
        "OCI_CONFIG_PROFILE": ("oci", "profile"),
        "OCI_LA_AUTH_TYPE": ("oci", "auth_type"),
        "OCI_LA_TIMEOUT": ("query", "timeout_seconds"),
        "OCI_LA_LOG_LEVEL": ("logging", "log_level"),
    }

    for env_var, (section, key) in env_mappings.items():
        if value := os.environ.get(env_var):
            section_obj = getattr(settings, section)

            # Handle type conversions
            if key == "config_path":
                value = Path(value)
            elif key == "timeout_seconds":
                value = int(value)

            setattr(section_obj, key, value)

    return settings


def save_config(settings: Settings, config_path: Optional[Path] = None) -> None:
    """Save settings to configuration file.

    Args:
        settings: Settings object to save.
        config_path: Optional path to config file. Uses default if not specified.
    """
    if config_path is None:
        config_path = CONFIG_PATH

    config_path.parent.mkdir(parents=True, exist_ok=True)

    data = settings.to_dict()
    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def config_exists(config_path: Optional[Path] = None) -> bool:
    """Check if configuration file exists.

    Args:
        config_path: Optional path to config file. Uses default if not specified.

    Returns:
        True if config file exists.
    """
    if config_path is None:
        config_path = CONFIG_PATH
    return config_path.exists()
