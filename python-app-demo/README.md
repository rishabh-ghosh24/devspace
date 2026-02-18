# OCI APM — Retail Quart Demo

A presales demo app showing end-to-end distributed tracing through OCI APM using pure OpenTelemetry auto-instrumentation. No code changes needed — the OTel wrapper does all the work.

## Architecture

```
[Browser]
    │ HTTP :80
    ▼
[VM1 — Apache httpd]          reverse proxy
    │ HTTP :8080 (private)
    ▼
[VM2 — Quart + Hypercorn]     async Python app
    │ SQLite
    ▼
[retail.db]                   products / customers / orders

Both VMs → OTel OTLP/HTTP → OCI APM
```

## OCI Security List Rules

| VM  | Port | Direction        | Why                        |
|-----|------|------------------|----------------------------|
| VM1 | 80   | Ingress (public) | Browser access             |
| VM2 | 8080 | Ingress (VM1 IP) | Apache → Quart             |
| Both| 443  | Egress           | OTel export → OCI APM      |

---

## VM1 — Apache Setup

```bash
# Install and enable Apache
sudo dnf install -y httpd git
sudo systemctl enable --now httpd
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload

# Clone the repo and check out the demo branch
git clone https://github.com/rishabh-ghosh24/devspace.git
cd devspace
git checkout python-app-demo

# Edit the config to set VM2's private IP before copying
vi python-app-demo/vm1-apache/quart-demo.conf
# Replace VM2_PRIVATE_IP with the actual private IP of pyapp2, then save

# Deploy config
sudo cp python-app-demo/vm1-apache/quart-demo.conf /etc/httpd/conf.d/quart-demo.conf
sudo systemctl reload httpd
```

---

## VM2 — Quart App Setup

### 1. Install system packages and clone repo

```bash
sudo dnf install -y python3.11 python3.11-pip sqlite git

# Clone the repo and check out the demo branch
git clone https://github.com/rishabh-ghosh24/devspace.git
cd devspace
git checkout python-app-demo
```

### 2. Deploy app files

```bash
sudo mkdir -p /opt/quart-demo
sudo cp python-app-demo/vm2-quart/{app.py,db.py,requirements.txt,start.sh} /opt/quart-demo/
sudo cp python-app-demo/vm2-quart/quart-demo.service /etc/systemd/system/
sudo chmod +x /opt/quart-demo/start.sh
sudo chown -R opc:opc /opt/quart-demo
```

### 3. Install Python dependencies

```bash
cd /opt/quart-demo
pip3.11 install -r requirements.txt
opentelemetry-bootstrap -a install   # installs instrumentors for detected libs
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

### 5. Enable and start the systemd service

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now quart-demo
sudo systemctl status quart-demo
```

---

## Verify it works

```bash
# From VM1 or any host with access
curl http://VM1_PUBLIC_IP/
curl http://VM1_PUBLIC_IP/products
curl http://VM1_PUBLIC_IP/products/1
curl http://VM1_PUBLIC_IP/products/category/Electronics
curl http://VM1_PUBLIC_IP/customers
curl http://VM1_PUBLIC_IP/orders
curl http://VM1_PUBLIC_IP/orders/slow   # intentionally takes ~2s
```

Then in **OCI APM Console**:
1. **Trace Explorer** → filter last 5 min → traces appear per route
2. **Topology** → `retail-quart-app` node with SQLite spans as children
3. **Slow Traces** → `/orders/slow` clearly stands out at ~2 000 ms

---

## App Routes (demo talking points)

| Route | What to show in APM |
|-------|---------------------|
| `GET /products` | Fast SELECT, clean single span |
| `GET /products/1` | Parameterised query — `db.statement` attribute |
| `GET /products/category/Electronics` | Filtered query span |
| `GET /customers` | Simple lookup |
| `GET /orders` | JOIN across 3 tables — rich `db.statement` |
| `GET /orders/slow` | 2 s artificial delay — latency spike in waterfall |

---

## Key OTel span attributes captured automatically

| Attribute | Example value |
|-----------|---------------|
| `http.method` | `GET` |
| `http.route` | `/products/{product_id}` |
| `http.status_code` | `200` |
| `db.system` | `sqlite` |
| `db.statement` | `SELECT * FROM products WHERE id = ?` |
| `net.peer.ip` | VM1 private IP |
| `service.name` | `retail-quart-app` |

---

## Troubleshooting

```bash
# Check app logs
sudo journalctl -u quart-demo -f

# Check Apache logs
sudo tail -f /var/log/httpd/quart-demo-error.log

# Test Quart directly (from VM2)
curl http://localhost:8080/products
```
