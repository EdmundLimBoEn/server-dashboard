# Server Dashboard

A refined, industrial-styled server monitoring dashboard with a distinctive terminal aesthetic. Self-hosted in Docker.

![Dashboard Preview](https://via.placeholder.com/800x400/0a0a0f/00ff9f?text=Server+Dashboard)

## Features

### Connectivity
- **Latency** - Ping to 1.1.1.1 and 8.8.8.8 with color-coded status dots (green/yellow/red)
- **Uptime** - Server uptime with boot timestamp
- **Tailscale IP** - Auto-detected Tailscale IP address

### System Resources
- **CPU** - Real-time usage with animated gradient progress bar
- **Memory** - RAM and Swap usage with combined progress indicator
- **Storage** - Disk usage with progress bar
- **Temperature** - CPU temperature via lm-sensors

### Services
- **Docker** - Running container count and status
- **Systemd** - Running services count with failed services warning
- **Load Average** - 1m, 5m, 15m load averages
- **Network I/O** - Bytes sent/received per interface

### Applications
- **Updates** - Upgradable packages list
- **Top Processes** - Top 5 processes by CPU usage

### UI/UX
- **Dark/Light Theme** - Toggle with ◐ button
- **Live Updates** - Auto-refreshes every 5 seconds with "Updated Xs ago" indicator
- **Refined Industrial Aesthetic** - IBM Plex Mono + DM Sans fonts, electric mint accent (#00ff9f)
- **Smooth Animations** - Staggered card fade-in, progress bar transitions
- **Responsive** - Works on desktop and mobile

## Quick Start

```bash
# Clone and run
git clone https://github.com/EdmundLimBoEn/server-dashboard.git
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

If your server has a different Tailscale IP range:
```yaml
environment:
  - FALLBACK_TAILSCALE_IP=100.x.x.x
```

### Port

The dashboard runs on port `0310` (mapped to internal port 310).
```yaml
ports:
  - "0310:310"  # Default
  # or
  - "8080:310"  # Custom external port
```

## Accessing the Dashboard

### Over Tailscale
`http://100.x.x.x:0310`

### Over LAN
`http://192.168.x.x:0310`

## Customization

### Alert Threshold
Edit `app.py`:
```python
ALERT_THRESHOLD = 90  # Percentage for alerts
```

### Refresh Interval
Edit `templates/index.html`:
```javascript
}, 5000);  // Change to preferred interval in ms
```

### Changing Colors
Edit CSS variables in `templates/index.html`:
```css
:root {
    --accent: #00ff9f;     /* Primary accent (electric mint) */
    --warning: #ffb800;    /* Warning color (amber) */
    --danger: #ff4757;     /* Danger color (coral) */
    --bg: #0a0a0f;         /* Background (deep charcoal) */
    --bg-card: #12121a;    /* Card background */
}
```

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

## Troubleshooting

### Temperature not showing
- Ensure `lm-sensors` is installed: `sudo apt install lm-sensors`
- Container needs `/dev` mounted for sensor access

### Docker stats not showing
- Currently blocked by AppArmor in container
- View via `docker stats` on the server

### Services count shows 0
- Systemd access requires `/run/systemd/system` mount
- If not needed, this is optional

## Requirements

- Docker & Docker Compose
- Linux server (tested on Ubuntu)
- Tailscale (optional, for remote access)

## Design

- **Typography**: IBM Plex Mono (headers), DM Sans (body)
- **Colors**: Deep charcoal background (#0a0a0f), electric mint accent (#00ff9f)
- **Style**: Refined industrial terminal aesthetic with subtle glows and smooth animations

## File Structure

```
server-dashboard/
├── app.py                   # FastAPI application
├── Dockerfile              # Container definition
├── docker-compose.yml       # Docker Compose config
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── templates/
    ├── index.html          # Dashboard UI
    └── fragments/          # HTMX partials (optional)
```

## License

MIT