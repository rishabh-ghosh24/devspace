# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Multi-project OCI observability and tooling repo. Each top-level directory is an independent project:

- **`mcp-servers/logan-mcp-server/`** — Python MCP server for OCI Log Analytics (active development on `oci-logan-mcp` branch)
- **`FinOps/`** — Terraform + OCI Function for FOCUS cost report automation
- **`logging/audit-log-masking/`** — OCI Function for audit log credential redaction
- **`monitoring/sla-report/`** — Python CLI for OCI Compute Availability Reports (SLA compliance, HTML output)
- **`monitoring/alarm-history-report/`** — OCI alarm history reporting
- **`python-app-demo/`** — StayEasy Hotel Booking app (Quart/Hypercorn + Oracle ADB) for OCI APM demos

## OCI Logan MCP Server

### Commands

```bash
cd mcp-servers/logan-mcp-server

# Install (development)
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# Run locally
python -m oci_logan_mcp

# Unit tests
pytest tests/ -v

# Single test file
pytest tests/test_config.py -v

# Integration tests (requires OCI access — run on VM)
python run_tests.py

# Lint & format
ruff check src/
black src/ tests/
mypy src/oci_logan_mcp/
```

### Architecture

The server communicates via MCP over stdio. Layers from top to bottom:

1. **`server.py`** — MCP lifecycle, tool/resource registration
2. **`handlers.py`** — Dispatches 20+ tool calls, orchestrates services
3. **Services** — `query_engine.py`, `schema_manager.py`, `validator.py`, `visualization.py`, `export.py`, `saved_search.py`
4. **`client.py`** — OCI Log Analytics SDK wrapper with rate limiting
5. **Supporting** — `config.py` (dataclasses + YAML/env loading), `auth.py` (3 auth modes), `cache.py` (in-memory TTL), `rate_limiter.py`, `query_logger.py`

All modules are flat under `src/oci_logan_mcp/` (no subpackages). Imports use `from .module import ...`.

### Key Design Decisions

- **Tenancy-wide queries** use a single API call with `compartment_id_in_subtree=True` at the tenancy OCID — same as the OCI Log Explorer UI "Subcompartments" checkbox. Do NOT iterate compartments individually.
- **Config hierarchy**: YAML file (`~/.oci-la-mcp/config.yaml`) → environment variables → defaults.
- **Auth modes**: `config_file` (local dev), `instance_principal` (OCI VMs), `resource_principal` (Functions).
- **`total_count` from OCI queries can be `None`** for aggregation queries (`stats count`). Always handle this — extract the count from `rows[0][0]` as fallback.
- **Package name is `oci_logan_mcp`** (not `oci_la_mcp` which was the old name).

### Deployment

The MCP server runs on an OCI VM (`130.61.171.71`) via SSH tunnel from Claude Desktop. The Claude Desktop config points to:
```
cd ~/devspace/mcp-servers/logan-mcp-server && source venv/bin/activate && python -m oci_logan_mcp
```

To deploy updates: push to `oci-logan-mcp` branch, then SSH to VM and `git pull && pip install -e .`

## Python APM Demo (StayEasy)

Two VMs: pyapp1 (Apache reverse proxy with OTel module) and pyapp2 (Quart app + Oracle ADB).

**Key pattern**: Zero OTel imports in `app.py`. All instrumentation lives in `otel_setup.py` and is bootstrapped via `asgi.py`. This demonstrates true auto-instrumentation for APM demos.

## Workflow Preferences

- Commit and push to **feature branches**, not main
- READMEs must include ALL setup steps (git clone, checkout, install) — never assume files exist on VMs
- Deployment scripts must be complete and idempotent
