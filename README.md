# GTGH — Graph Traffic GitHub

Monitoring stack that collects public GitHub repository traffic (views & clones) and displays them in a Grafana dashboard.

---

## How it works

```
GitHub API
    │
    ▼
github-exporter (Python/Flask)
    │  ├── exposes /metrics  ──► Prometheus (scrapes every hour)
    │  └── persists history  ──► SQLite (traffic_data.db)
                                          │
                                    Grafana ◄─────────────────┘
                                  (dashboard on :3000)
```

Three services run together via Podman Compose:

| Service | Image | Role |
|---|---|---|
| `github-exporter` | custom Python | fetches GitHub API, exposes Prometheus metrics |
| `prometheus` | `prom/prometheus` | scrapes and stores metrics for 90 days |
| `grafana` | `grafana/grafana` | dashboard, auto-provisioned |

Metrics are collected every hour. GitHub's own traffic API refreshes at most once per 24h, so sub-hourly polling adds no value.

---

## Requirements

- [Podman](https://podman.io/docs/installation) >= 4.x
- [podman-compose](https://github.com/containers/podman-compose) >= 1.x
- A GitHub **personal access token** with the `repo` scope (read access to traffic data)

### Install podman-compose

```bash
pip install podman-compose
```

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd GTGH
```

### 2. Create the `.env` file

```bash
cp .env.example .env   # if available, otherwise create manually
```

Required variables:

```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GF_SECURITY_ADMIN_PASSWORD=your_grafana_password
DEBUG=0
```

| Variable | Description |
|---|---|
| `GITHUB_TOKEN` | GitHub personal access token (scope: `repo`) |
| `GF_SECURITY_ADMIN_PASSWORD` | Grafana admin password |
| `DEBUG` | Set to `1` for verbose output (optional) |

### 3. Start the stack

```bash
podman-compose up -d
```

Grafana is available at **http://\<raspberry-ip\>:3000**
Login: `admin` / your `GF_SECURITY_ADMIN_PASSWORD`

---

## Dashboard

The dashboard **GitHub Traffic** is provisioned automatically at startup. No manual configuration required.

| Panel | Description |
|---|---|
| Total projects | Number of public repositories monitored |
| Average views | Mean unique views across all repositories |
| Average clones | Mean unique clones across all repositories |
| Projects exceeding 100 views | Table, highlighted in red |
| Projects exceeding 20 clones | Table, highlighted in red |

---

## Metrics

The exporter exposes two Prometheus gauges at `http://<host>:8000/metrics`:

| Metric | Label | Description |
|---|---|---|
| `github_repo_views` | `repo` | Unique views for the repository |
| `github_repo_clones` | `repo` | Unique clones for the repository |

---

## Data retention

| Storage | Retention |
|---|---|
| Prometheus TSDB | 90 days |
| SQLite (`traffic_data.db`) | permanent — one row per repository per day |

---

## Hardware target — Raspberry Pi 4 Model B (4 CPU / 4 GB RAM)

The resource limits are tuned for this board:

| Service | CPU limit | RAM limit |
|---|---|---|
| github-exporter | 0.50 | 256 MB |
| prometheus | 0.75 | 256 MB |
| grafana | 0.50 | 192 MB |
| **Total** | **1.75** | **704 MB** |

WAL compression is enabled on Prometheus (`--storage.tsdb.wal-compression`) and Grafana telemetry/analytics are disabled to reduce idle RAM usage.

### Auto-start on boot (Podman rootless)

`podman-compose` does not persist restarts across reboots on its own. To make the stack start automatically with systemd:

```bash
podman-compose up -d
podman generate systemd --new --name github_exporter > ~/.config/systemd/user/github-exporter.service
systemctl --user enable --now github-exporter.service
loginctl enable-linger $USER
```

---

## Stop the stack

```bash
podman-compose down
```

Data volumes (`prometheus-data`, `grafana-data`, `traffic_data.db`) are preserved.
