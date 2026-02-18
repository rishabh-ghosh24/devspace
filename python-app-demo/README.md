# OCI APM — StayEasy Hotel Booking Demo

A presales demo showing end-to-end distributed tracing through OCI APM. The application code (`app.py`) contains **zero OpenTelemetry imports** — all tracing is wired externally via `otel_setup.py` and `asgi.py`, demonstrating true auto-instrumentation for Python/Quart.

## Architecture

```
[Browser / curl]
    │ HTTP :80
    ▼
[VM1 — Apache httpd]          reverse proxy
    │ HTTP :8080 (private)
    ▼
[VM2 — Hypercorn]             ASGI server
    │
    ├── asgi.py               ← OTel init + ASGI middleware (entry point)
    ├── otel_setup.py         ← all OTel config (exporter, instrumentors)
    ├── app.py                ← 100% business logic, ZERO OTel imports
    ├── db.py                 ← SQLite schema + seed data
    │       │
    │       ▼
    │   [hotel.db]            5 tables: hotels, rooms, guests, reservations, payments
    │
    └──→ OTel OTLP/HTTP ──→ OCI APM
```

## OCI Security List Rules

| VM  | Port | Direction        | Why                   |
|-----|------|------------------|-----------------------|
| VM1 | 80   | Ingress (public) | Browser access        |
| VM2 | 8080 | Ingress (VM1 IP) | Apache → Quart        |
| Both| 443  | Egress           | OTel export → OCI APM |

## Prerequisites

- Enable SELinux network connect on VM1: `sudo setsebool -P httpd_can_network_connect 1`
- Open firewall on VM2: `sudo firewall-cmd --permanent --add-port=8080/tcp && sudo firewall-cmd --reload`

---

## VM1 — Apache Setup

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

---

## VM2 — Quart App Setup

### 1. Install system packages and clone repo

```bash
sudo dnf install -y python3.11 python3.11-pip sqlite git

git clone https://github.com/rishabh-ghosh24/devspace.git
cd devspace
git checkout python-app-demo
```

### 2. Deploy app files

```bash
sudo mkdir -p /opt/quart-demo
sudo cp python-app-demo/vm2-quart/{app.py,db.py,otel_setup.py,asgi.py,requirements.txt,start.sh} /opt/quart-demo/
sudo cp python-app-demo/vm2-quart/quart-demo.service /etc/systemd/system/
sudo chmod +x /opt/quart-demo/start.sh
sudo chown -R opc:opc /opt/quart-demo
```

### 3. Install Python dependencies

```bash
cd /opt/quart-demo
pip3.11 install -r requirements.txt
opentelemetry-bootstrap -a install
```

### 4. Create the environment file

```bash
cat <<EOF | sudo tee /opt/quart-demo/.env
APM_ENDPOINT=https://<your-apm-domain-prefix>.apm-agt.<region>.oci.oraclecloud.com
APM_DATA_KEY=<your-private-data-key>
EOF
sudo chown opc:opc /opt/quart-demo/.env
sudo chmod 640 /opt/quart-demo/.env
```

> Get these values from **OCI Console → Observability & Management → APM → your domain → Data Keys**.

### 5. Open firewall and start service

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

| Route | Method | Spans | What to show in APM |
|-------|--------|-------|---------------------|
| `/` | GET | 1 | Health check |
| `/hotels` | GET | 2 | Simple query + HTTP span |
| `/hotels/<id>` | GET | 3 | Hotel detail + rooms (2 DB queries) |
| `/hotels/<id>/rooms` | GET | 2 | Room listing |
| `/rooms/search?...` | GET | **10+** | Complex search: per-room availability checks |
| `/reservations` | POST | **6** | Multi-step booking: validate → check → insert → pay |
| `/reservations/<id>` | GET | 2 | 4-table JOIN with rich `db.statement` |
| `/guests/<id>/reservations` | GET | 3 | Booking history |
| `/reports/occupancy` | GET | 2 | **1.5 s latency spike** in APM waterfall |
| `/reports/revenue` | GET | 2 | Revenue aggregate |

## Key Design: Zero OTel in app.py

```
asgi.py          → calls init_otel() then wraps app with ASGI middleware
otel_setup.py    → TracerProvider, OTLP exporter, SQLite3Instrumentor
app.py           → pure Quart business logic — grep for "opentelemetry" returns 0 matches
```

The customer can verify: `grep -c opentelemetry app.py` → **0**

## OTel Span Attributes (captured automatically)

| Attribute | Example |
|-----------|---------|
| `http.method` | `POST` |
| `http.target` | `/reservations` |
| `http.status_code` | `201`, `409` |
| `db.system` | `sqlite` |
| `db.statement` | `INSERT INTO reservations ...` |
| `service.name` | `stayeasy-hotel-app` |

---

## Troubleshooting

```bash
# App logs
sudo journalctl -u quart-demo -f

# Apache logs
sudo tail -f /var/log/httpd/quart-demo-error.log

# Test Quart directly from VM2
curl http://localhost:8080/hotels

# Delete DB to re-seed
sudo rm /opt/quart-demo/hotel.db
sudo systemctl restart quart-demo
```
