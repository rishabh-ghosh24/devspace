# OCI APM — StayEasy Hotel Booking Demo

A presales demo showing end-to-end distributed tracing through OCI APM. The application code (`app.py`) contains **zero OpenTelemetry imports** — all tracing is wired externally via `otel_setup.py` and `asgi.py`, demonstrating true auto-instrumentation for Python/Quart.

## Architecture

```
[Browser / curl]
    │ HTTP :80
    ▼
[VM1 — Apache httpd]          reverse proxy (pyapp1)
    │  service: stayeasy-webserver
    │  OTel Apache module → OTel Collector → OCI APM
    │  auto-injects traceparent header
    │ HTTP :8080 (private)
    ▼
[VM2 — Hypercorn]             ASGI server (pyapp2)
    │  service: stayeasy-hotel-app
    │
    ├── asgi.py               ← OTel init + ASGI middleware (entry point)
    ├── otel_setup.py         ← all OTel config (exporter, oracledb instrumentor)
    ├── app.py                ← 100% business logic, ZERO OTel imports
    ├── db.py                 ← Oracle ADB connection (thin mode, TLS)
    │       │
    │       ▼
    │   [Oracle ADB]          peer.service: oracle-adb
    │                         5 tables: hotels, rooms, guests, reservations, payments
    │
    └──→ OTel OTLP/HTTP ──→ OCI APM

APM Topology: stayeasy-webserver → stayeasy-hotel-app → oracle-adb
```

## Prerequisites

### OCI Resources
- **2 Compute VMs** (OEL 9): pyapp1 (Apache), pyapp2 (Quart)
- **Oracle ADB** (Developer or any tier): mTLS not required (TLS wallet-less)
- **OCI APM Domain** with a private data key

### Networking
| Resource | Port | Direction | Why |
|----------|------|-----------|-----|
| VM1 | 80 | Ingress (public) | Browser access |
| VM2 | 8080 | Ingress (VM1 private IP) | Apache → Quart |
| Both | 443 | Egress | OTel export → OCI APM |
| ADB | 1521 | Egress from VM2 | Quart → ADB (TLS) |

- pyapp2's **public IP** must be in the ADB Access Control List
- ADB must have **mTLS set to "Not required"** (TLS authentication enabled)

---

## Step 1 — ADB Schema Setup

Run this from any machine with Python 3.11 and network access to ADB.

```bash
pip3.11 install oracledb

# Clone the repo
git clone https://github.com/rishabh-ghosh24/devspace.git
cd devspace
git checkout python-app-demo

# Run schema setup (creates STAYEASY user, tables, and seed data)
python3.11 python-app-demo/vm2-quart/setup_schema.py \
  --dsn '(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1521)(host=adb.eu-frankfurt-1.oraclecloud.com))(connect_data=(service_name=<your_service_name>.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))' \
  --admin-password 'YourAdminPassword' \
  --app-password 'YourStayEasyPassword'
```

> **Get the DSN:** ADB Console → Database connection → TLS authentication: TLS → copy the `myadb_medium` connection string.

The script is idempotent — safe to re-run. Use `--drop` to destroy and recreate.

---

## Step 2 — VM1 (Apache) Setup

```bash
sudo dnf install -y httpd git
sudo systemctl enable --now httpd
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
sudo setsebool -P httpd_can_network_connect 1

git clone https://github.com/rishabh-ghosh24/devspace.git
cd devspace
git checkout python-app-demo

# Edit the config — replace VM2_PRIVATE_IP with pyapp2's private IP
vi python-app-demo/vm1-apache/quart-demo.conf

sudo cp python-app-demo/vm1-apache/quart-demo.conf /etc/httpd/conf.d/quart-demo.conf
sudo systemctl reload httpd
```

### 2b. Install OpenTelemetry Apache module (optional — enables 3-service topology)

This installs the OTel Apache module so Apache appears as `stayeasy-webserver` in APM and auto-injects `traceparent` headers.

```bash
# Run the install script (downloads otel-webserver-module v1.1.0)
sudo bash python-app-demo/vm1-apache/install-otel-apache.sh

# Copy the Apache OTel module config
sudo cp python-app-demo/vm1-apache/opentelemetry_module.conf /etc/httpd/conf.d/

# Install OTel Collector (bridges gRPC from Apache module → OTLP/HTTP to APM)
curl -fSL https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.96.0/otelcol_0.96.0_linux_amd64.tar.gz -o /tmp/otelcol.tar.gz
sudo mkdir -p /opt/otel-collector
sudo tar -xzf /tmp/otelcol.tar.gz -C /opt/otel-collector/

# Copy and edit collector config — replace 3 placeholders:
#   <APM_DOMAIN>            → your APM domain prefix (e.g., abcdef123456)
#   <REGION>                → OCI region (e.g., eu-frankfurt-1)
#   <YOUR_PRIVATE_DATA_KEY> → APM private data key
sudo cp python-app-demo/vm1-apache/otel-collector-config.yaml /opt/otel-collector/
sudo vi /opt/otel-collector/otel-collector-config.yaml

# Deploy and start the collector as a systemd service
sudo cp python-app-demo/vm1-apache/otel-collector.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now otel-collector
sudo journalctl -u otel-collector --no-pager -n 5

# Restart Apache to load the OTel module
sudo systemctl restart httpd
httpd -M | grep otel   # Should show: otel_apache_module (shared)
```

---

## Step 3 — VM2 (Quart App) Setup

### 3a. Install system packages and clone repo

```bash
sudo dnf install -y python3.11 python3.11-pip git

git clone https://github.com/rishabh-ghosh24/devspace.git
cd devspace
git checkout python-app-demo
```

### 3b. Deploy app files

```bash
sudo mkdir -p /opt/quart-demo
sudo cp python-app-demo/vm2-quart/{app.py,db.py,otel_setup.py,asgi.py,requirements.txt,start.sh} /opt/quart-demo/
sudo cp python-app-demo/vm2-quart/quart-demo.service /etc/systemd/system/
sudo chmod +x /opt/quart-demo/start.sh
sudo chown -R opc:opc /opt/quart-demo
```

### 3c. Install Python dependencies

```bash
cd /opt/quart-demo
pip3.11 install -r requirements.txt
```

### 3d. Create the environment file

```bash
cat <<'EOF' | sudo tee /opt/quart-demo/.env
APM_ENDPOINT=https://<your-apm-domain-prefix>.apm-agt.<region>.oci.oraclecloud.com
APM_DATA_KEY=<your-private-data-key>
DB_DSN=(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1521)(host=adb.<region>.oraclecloud.com))(connect_data=(service_name=<service_name>.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))
DB_USER=stayeasy
DB_PASSWORD=<YourStayEasyPassword>
EOF
sudo chown opc:opc /opt/quart-demo/.env
sudo chmod 640 /opt/quart-demo/.env
```

> **APM values:** OCI Console → Observability & Management → APM → your domain → Data Keys.
> **DB_DSN:** ADB Console → Database connection → TLS → copy `myadb_medium` connection string.

### 3e. Open firewall and start service

```bash
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
sudo systemctl daemon-reload
sudo systemctl enable --now quart-demo
sudo systemctl status quart-demo
```

---

## Verify It Works

```bash
# Health check
curl http://VM1_PUBLIC_IP/

# Hotels
curl http://VM1_PUBLIC_IP/hotels
curl http://VM1_PUBLIC_IP/hotels/1

# Search available rooms (generates 10+ DB spans)
curl "http://VM1_PUBLIC_IP/rooms/search?city=London&check_in=2025-05-01&check_out=2025-05-05&guests=2"

# Book a room (THE MONEY ROUTE — 6 DB spans)
curl -X POST http://VM1_PUBLIC_IP/reservations \
  -H "Content-Type: application/json" \
  -d '{"guest_id":1,"room_id":4,"check_in":"2025-05-01","check_out":"2025-05-05","payment_method":"credit_card"}'

# View reservation (4-table JOIN)
curl http://VM1_PUBLIC_IP/reservations/7

# Try double-booking same room/dates → 409 Conflict (error trace)
curl -X POST http://VM1_PUBLIC_IP/reservations \
  -H "Content-Type: application/json" \
  -d '{"guest_id":2,"room_id":4,"check_in":"2025-05-03","check_out":"2025-05-06","payment_method":"credit_card"}'

# Guest booking history
curl http://VM1_PUBLIC_IP/guests/1/reservations

# Slow report (~1.5 s — shows latency in APM)
curl http://VM1_PUBLIC_IP/reports/occupancy

# Revenue report
curl http://VM1_PUBLIC_IP/reports/revenue
```

---

## Routes & Demo Talking Points

| Route | Method | DB Spans | What to show in APM |
|-------|--------|----------|---------------------|
| `/` | GET | 0 | Health check (ASGI span only) |
| `/hotels` | GET | 1 | Simple SELECT + full `db.statement` visible |
| `/hotels/<id>` | GET | 2 | Hotel + rooms (2 Oracle queries) |
| `/hotels/<id>/rooms` | GET | 1 | Room listing |
| `/rooms/search?...` | GET | **10+** | Complex search: per-room availability checks |
| `/reservations` | POST | **6** | Multi-step booking: validate → check → INSERT → pay |
| `/reservations/<id>` | GET | 1 | 4-table JOIN with rich `db.statement` |
| `/guests/<id>/reservations` | GET | 2 | Booking history |
| `/reports/occupancy` | GET | 1 | **1.5 s latency spike** in APM waterfall |
| `/reports/revenue` | GET | 1 | Revenue aggregate |

## Key Design: Zero OTel in app.py

```
asgi.py          → calls init_otel() then wraps app with ASGI middleware
otel_setup.py    → TracerProvider, OTLP exporter, oracledb DB-API instrumentor
app.py           → pure Quart business logic — grep for "opentelemetry" returns 0 matches
```

The customer can verify: `grep -c opentelemetry app.py` → **0**

## OTel Span Attributes (captured automatically)

| Attribute | Example |
|-----------|---------|
| `http.method` | `POST` |
| `http.target` | `/reservations` |
| `http.status_code` | `201`, `409` |
| `db.system` | `oracle` |
| `db.statement` | `SELECT * FROM hotels ORDER BY rating DESC` |
| `db.operation` | `SELECT`, `INSERT` |
| `peer.service` | `oracle-adb` (DB spans) |
| `service.name` | `stayeasy-hotel-app` (Quart), `stayeasy-webserver` (Apache) |

---

## Troubleshooting

```bash
# App logs
sudo journalctl -u quart-demo -f

# Apache logs
sudo tail -f /var/log/httpd/quart-demo-error.log

# Test Quart directly from VM2
curl http://localhost:8080/hotels

# Test ADB connectivity from VM2
python3.11 -c "
import oracledb, os
conn = oracledb.connect(user='stayeasy', password=os.environ['DB_PASSWORD'], dsn=os.environ['DB_DSN'])
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM hotels')
print('Hotels:', cur.fetchone()[0])
conn.close()
"

# Re-run schema setup (idempotent)
python3.11 setup_schema.py --dsn '...' --admin-password '...' --app-password '...'

# Full reset (drop and recreate)
python3.11 setup_schema.py --dsn '...' --admin-password '...' --app-password '...' --drop
```
