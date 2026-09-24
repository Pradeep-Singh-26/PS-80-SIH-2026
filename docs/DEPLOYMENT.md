# 🚀 Deployment Guide — PS-80 AI Post-Processing System

This guide outlines production deployment strategies for the **Regime-Aware AI Post-Processing System for Monsoon Rainfall Forecasts**. The system consists of two primary operational services:
1. **REST API Backend** (`FastAPI` running on Uvicorn, default port `8000`)
2. **Interactive Web Dashboard** (`Streamlit`, default port `8501`)

---

## 📋 Table of Contents
- [Prerequisites & System Requirements](#-prerequisites--system-requirements)
- [Environment Configuration](#-environment-configuration)
- [Option 1: Docker Compose Deployment (Recommended)](#option-1-docker-compose-deployment-recommended)
- [Option 2: Cloud Virtual Machine (Ubuntu / Debian / AWS EC2)](#option-2-cloud-virtual-machine-ubuntu--debian--aws-ec2)
- [Option 3: Streamlit Community Cloud / Hosted Dashboard](#option-3-streamlit-community-cloud--hosted-dashboard)
- [Nginx Reverse Proxy & SSL Setup](#nginx-reverse-proxy--ssl-setup)
- [Operational Health Checks & Monitoring](#operational-health-checks--monitoring)
- [Troubleshooting & FAQs](#troubleshooting--faqs)

---

## 💻 Prerequisites & System Requirements

### Hardware Requirements
| Resource | Minimum (Inference & Dashboard) | Recommended (Full Pipeline Execution) |
|---|---|---|
| **CPU** | 2 vCPUs | 4–8 vCPUs |
| **RAM** | 4 GB | 16 GB |
| **Disk Storage** | 10 GB SSD | 50+ GB SSD (for multi-year NetCDF grids) |
| **OS** | Linux (Ubuntu 20.04+), macOS, Windows 10/11 | Linux (Ubuntu 22.04 LTS recommended) |

### Software Dependencies
- **Python**: `3.10` to `3.12`
- **Docker**: Engine `v20.10+` and Docker Compose `v2.0+`
- **System Libraries**: `libgdal-dev`, `libgeos-dev`, `libproj-dev` (if compiling geospatial C-extensions from source)

---

## 🔑 Environment Configuration

Create a production `.env` file in the repository root directory (this file is ignored by Git):

```bash
# ==========================================
# PS-80 Production Environment Configuration
# ==========================================

# 1. API Keys for Topography & Geospatial Services
CARTODEM_API_KEY=your_cartodem_api_key_here
BHUVAN_API_KEY=your_bhuvan_api_key_here

# 2. Master Pipeline Configuration File
CONFIG_PATH=config.yaml

# 3. Server Binding Configurations
API_HOST=0.0.0.0
API_PORT=8000
DASHBOARD_PORT=8501

# 4. Service Discovery
API_URL=http://localhost:8000

# 5. Logging Level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

> [!IMPORTANT]
> Never commit `.env` into public version control. Ensure `.env` is listed inside `.gitignore`.

---

## 🐳 Option 1: Docker Compose Deployment (Recommended)

Docker Compose containerizes both the FastAPI service and the Streamlit dashboard into isolated, lightweight environments with shared access to model outputs and datasets.

### 1. Build and Run Services
Navigate to `infra/docker/` and launch the containers in detached mode:

```bash
cd infra/docker
docker-compose up --build -d
```

### 2. Verify Container Health
```bash
docker-compose ps
```

Expected output:
```text
NAME                     IMAGE                    COMMAND                  SERVICE             STATUS              PORTS
ps80-api-1              ps80-api                 "uvicorn api.main:..."   api                 running (healthy)   0.0.0.0:8000->8000/tcp
ps80-dashboard-1        ps80-dashboard           "streamlit run dash..."  dashboard           running (healthy)   0.0.0.0:8501->8501/tcp
```

### 3. Access Services
- **Web Dashboard**: [http://localhost:8501](http://localhost:8501)
- **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### 4. Stop and Restart
```bash
# Stop all services
docker-compose down

# View logs in real-time
docker-compose logs -f
```

---

## ☁️ Option 2: Cloud Virtual Machine (Ubuntu / Debian / AWS EC2)

Follow these steps to deploy bare-metal on an Ubuntu 22.04 LTS instance:

### Step 1: System Packages and Environment
```bash
sudo apt-get update && sudo apt-get install -y \
    python3-pip \
    python3-venv \
    git \
    curl \
    build-essential \
    libgdal-dev

# Clone repository
git clone https://github.com/your-org/PS-80-SIH-2026.git
cd PS-80-SIH-2026

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Run End-to-End Pipeline
Generate initial model weights, regime classifications, bias corrections, and verification outputs:

```bash
# Run against standard config
python run_pipeline.py --config config.test.yaml
```

### Step 3: Configure Systemd Services
To ensure high availability and auto-restart on boot, create systemd service unit files.

#### API Unit File: `/etc/systemd/system/ps80-api.service`
```ini
[Unit]
Description=PS-80 Weather AI FastAPI Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/PS-80-SIH-2026
EnvironmentFile=/home/ubuntu/PS-80-SIH-2026/.env
ExecStart=/home/ubuntu/PS-80-SIH-2026/venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### Dashboard Unit File: `/etc/systemd/system/ps80-dashboard.service`
```ini
[Unit]
Description=PS-80 Weather AI Streamlit Dashboard
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/PS-80-SIH-2026
EnvironmentFile=/home/ubuntu/PS-80-SIH-2026/.env
ExecStart=/home/ubuntu/PS-80-SIH-2026/venv/bin/streamlit run dashboard/web/app.py --server.port 8501 --server.headless true --server.enableCORS false
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### Enable and Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ps80-api
sudo systemctl enable --now ps80-dashboard

# Check operational status
sudo systemctl status ps80-api
sudo systemctl status ps80-dashboard
```

---

## 🌐 Nginx Reverse Proxy & SSL Setup

To serve the dashboard and API over HTTPS on standard web ports (`80` and `443`):

### 1. Install Nginx and Certbot
```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

### 2. Nginx Site Configuration (`/etc/nginx/sites-available/ps80`)
```nginx
server {
    listen 80;
    server_name weather-ai.yourdomain.gov.in;

    # Streamlit Web Dashboard
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # FastAPI REST API & Swagger UI
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_set_header Host $host;
    }
}
```

### 3. Enable Site & Request SSL Certificate
```bash
sudo ln -s /etc/nginx/sites-available/ps80 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo certbot --nginx -d weather-ai.yourdomain.gov.in
```

---

## 📊 Operational Health Checks & Monitoring

The REST API provides built-in observability endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/health` | `GET` | Instant liveness probe for load balancers (`{"status": "ok"}`) |
| `/api/v1/meta` | `GET` | System configuration, available date ranges, and feature stats |
| `/api/v1/cache/clear` | `POST` | Flushes in-memory data caches after scheduled pipeline re-runs |

### Automated Cron Job for Daily Pipeline Runs
Add a daily cron job to execute the pipeline when new operational NWP forecasts arrive (e.g. 06:00 UTC):

```bash
crontab -e
```
```cron
0 6 * * * cd /home/ubuntu/PS-80-SIH-2026 && /home/ubuntu/PS-80-SIH-2026/venv/bin/python run_pipeline.py >> /var/log/ps80_pipeline.log 2>&1 && curl -X POST http://localhost:8000/api/v1/cache/clear
```

---

## 🛠️ Troubleshooting & FAQs

### Q1: Streamlit Dashboard shows "Connection Error" when calling API
- Verify FastAPI is running: `curl http://127.0.0.1:8000/api/v1/health`.
- If running in Docker, ensure the dashboard container references `http://api:8000` via Docker network DNS, not `localhost`.

### Q2: CartoDEM / Bhuvan elevation data shows "missing API key"
- Confirm `.env` has valid credentials for `CARTODEM_API_KEY` and `BHUVAN_API_KEY`.
- Test status via `curl http://127.0.0.1:8000/api/v1/topography/cartodem`.

### Q3: How to test the system in an isolated testing environment?
- Run `python run_pipeline.py --config config.test.yaml`.
- Run automated unit tests: `python -m pytest -q`.
