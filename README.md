# Server Dashboard

A simple, self-hosted server monitoring dashboard running in Docker.

## Features

- **Ping** - Latency to 1.1.1.1 and 8.8.8.8
- **Uptime** - Server uptime
- **Tailscale IP** - Your Tailscale IP address (auto-detected)
- **CPU/RAM/Disk** - Real-time usage with progress bars
- **Temperature** - CPU temperature (via lm-sensors)
- **Network Traffic** - Bytes sent/received per interface
- **Upgradable Packages** - List of packages that can be updated
- **Top Processes** - Top 5 processes by CPU usage
- **Dark/Light Theme** - Toggle button in header
- **Auto-refresh** - Updates every 5 seconds without layout shift
- **Alerts** - Warning when CPU or RAM exceeds 90%

## Quick Start

```bash
# Clone and run
git clone <your-repo>/server-dashboard.git
cd server-dashboard
docker compose up -d
```

Access at: `http://<your-server-ip>:0310`

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DASHBOARD_TITLE` | `Server Dashboard` | Title shown in browser and header |
| `FALLBACK_TAILSCALE_IP` | `100.83.252.53` | Fallback IP if auto-detection fails |

### Changing the Title

Edit `docker-compose.yml`:
```yaml
environment:
  - DASHBOARD_TITLE=My Server
```

### Changing the Fallback Tailscale IP

If your server has a different Tailscale IP range, set:
```yaml
environment:
  - FALLBACK_TAILSCALE_IP=100.x.x.x
```

### Port

The dashboard runs on port `0310` (mapped to internal port 310).

## Accessing the Dashboard

### Over Tailscale
Access using your Tailscale IP: `http://100.x.x.x:0310`

### Over LAN
Access using your server's LAN IP: `http://192.168.x.x:0310`

## Updating

```bash
cd server-dashboard
git pull
docker compose build
docker compose up -d
```

## Stopping

```bash
docker compose down
```

## Customization

### Alert Threshold
Edit `app.py` to change the alert percentage (default: 90%):
```python
ALERT_THRESHOLD = 90  # Change this value
```

### Refresh Interval
The dashboard auto-refreshes every 5 seconds. To change, edit `templates/index.html`:
```javascript
setInterval(async function() {
    // Change 5000 to your preferred interval in ms
}, 5000);
```

## Troubleshooting

### Temperature not showing
- Ensure `lm-sensors` is installed on the host: `sudo apt install lm-sensors`
- The container needs `/dev` mounted for sensor access

### Docker stats not showing
- Currently blocked by AppArmor in container
- Workaround: View via `docker stats` on the server

### Tailscale IP not detected
- Set the fallback IP in environment variables
- Or run `ip addr show` on server to verify Tailscale interface

### Port already in use
- Change the port in `docker-compose.yml`:
  ```yaml
  ports:
    - "8080:310"  # Now accessible at port 8080
  ```

## Requirements

- Docker & Docker Compose
- Linux server (tested on Ubuntu)
- Tailscale (optional, for remote access)

## File Structure

```
server-dashboard/
├── app.py              # FastAPI application
├── Dockerfile          # Container definition
├── docker-compose.yml # Docker Compose config
├── requirements.txt   # Python dependencies
├── templates/
│   └── index.html     # Dashboard UI
└── README.md          # This file
```