import os
import socket
import subprocess
import time
from collections import deque
from datetime import datetime, timezone, timedelta
from functools import lru_cache

TZ = timezone(timedelta(hours=8))

DASHBOARD_TITLE = os.environ.get("DASHBOARD_TITLE", "Server Dashboard")
FALLBACK_TAILSCALE_IP = os.environ.get("FALLBACK_TAILSCALE_IP", "100.83.252.53")

import psutil
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

app = FastAPI()
jinja_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html", "xml"]),
)

MAX_HISTORY = 60
cpu_history = deque(maxlen=MAX_HISTORY)
ram_history = deque(maxlen=MAX_HISTORY)

ALERT_THRESHOLD = 90
alerts = []


def get_uptime():
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    return f"{days}d {hours}h {minutes}m"


def get_loadavg():
    load1, load5, load15 = os.getloadavg()
    return {"1m": round(load1, 2), "5m": round(load5, 2), "15m": round(load15, 2)}


def get_tailscale_ip():
    try:
        result = subprocess.run(
            ["ip", "addr", "show"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.split("\n"):
            parts = line.split()
            if len(parts) >= 2 and parts[0] == "inet":
                addr = parts[1]
                if addr.startswith("100."):
                    return addr.split("/")[0]
    except Exception:
        pass
    return FALLBACK_TAILSCALE_IP


def ping_host(host, count=1):
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", "2", host],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "time=" in line:
                    time_ms = line.split("time=")[1].split()[0]
                    return float(time_ms)
    except Exception:
        pass
    return None


def get_pings():
    hosts = [
        ("1.1.1.1", "Cloudflare"),
        ("8.8.8.8", "Google"),
    ]
    results = []
    for host, name in hosts:
        ms = ping_host(host)
        if ms is not None:
            results.append({"host": host, "name": name, "ms": round(ms, 1)})
    return results


def get_temperature():
    try:
        result = subprocess.run(
            ["sensors", "-u"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        temps = []
        for line in result.stdout.split("\n"):
            if "temp1_input" in line or "temp2_input" in line or "temp3_input" in line or "temp4_input" in line or "temp5_input" in line:
                try:
                    temp = float(line.split(":")[1].strip())
                    if temp > 0 and temp < 150:
                        temps.append(round(temp, 1))
                except:
                    pass
        if temps:
            return list(set(temps))[:4]
    except Exception:
        pass
    
    try:
        result = subprocess.run(
            ["cat", "/sys/class/thermal/thermal_zone0/temp"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            temp = int(result.stdout.strip()) / 1000
            return [round(temp, 1)]
    except Exception:
        pass
    return []


def get_failed_services():
    try:
        result = subprocess.run(
            ["systemctl", "list-units", "--failed", "--no-pager", "--plain"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")[1:]
            services = []
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 1:
                        services.append(parts[0])
            return services[:5]
    except Exception:
        pass
    return []


def get_docker_stats():
    try:
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.Name}},{{.CPUPerc}},{{.MemPerc}},{{.MemUsage}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            containers = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split(",")
                    if len(parts) >= 4:
                        containers.append({
                            "name": parts[0],
                            "cpu": parts[1].strip().replace("%", ""),
                            "mem": parts[2].strip().replace("%", ""),
                            "mem_usage": parts[3].strip(),
                        })
            return containers
    except Exception:
        pass
    return []


def get_network_traffic():
    counters = psutil.net_io_counters(pernic=True)
    traffic = {}
    for iface, counters in counters.items():
        if iface in ["eth0", "ens", "tailscale0", "docker0"]:
            traffic[iface] = {
                "bytes_sent": counters.bytes_sent // (1024**2),
                "bytes_recv": counters.bytes_recv // (1024**2),
            }
    return traffic


def get_upgradable_packages():
    try:
        result = subprocess.run(
            ["apt", "list", "--upgradable"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")[1:]
            packages = []
            for line in lines:
                if line:
                    parts = line.split(" ")
                    if len(parts) >= 2:
                        packages.append(parts[0])
            return packages[:10]
    except Exception:
        pass
    return []


def get_system_stats():
    global alerts
    alerts = []
    
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu_percent = psutil.cpu_percent(interval=None)
    
    cpu_history.append(cpu_percent)
    ram_history.append(vm.percent)
    
    if vm.percent > ALERT_THRESHOLD:
        alerts.append(f"RAM at {vm.percent}%")
    if cpu_percent > ALERT_THRESHOLD:
        alerts.append(f"CPU at {cpu_percent}%")
    
    processes = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            if info["cpu_percent"] and info["cpu_percent"] > 0:
                processes.append(
                    {
                        "name": info["name"],
                        "pid": info["pid"],
                        "cpu": round(info["cpu_percent"], 1),
                        "mem": round(info["memory_percent"], 1),
                    }
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    processes.sort(key=lambda x: x["cpu"], reverse=True)
    top_processes = processes[:5]

    return {
        "cpu": cpu_percent,
        "ram_used": vm.used // (1024**3),
        "ram_total": vm.total // (1024**3),
        "ram_percent": vm.percent,
        "disk_used": disk.used // (1024**3),
        "disk_total": disk.total // (1024**3),
        "disk_percent": disk.percent,
        "uptime": get_uptime(),
        "load": get_loadavg(),
        "tailscale_ip": get_tailscale_ip(),
        "pings": get_pings(),
        "upgradable_packages": get_upgradable_packages(),
        "top_processes": top_processes,
        "temperature": get_temperature(),
        "failed_services": get_failed_services(),
        "docker_stats": get_docker_stats(),
        "network_traffic": get_network_traffic(),
        "alerts": alerts,
        "cpu_history": list(cpu_history),
        "ram_history": list(ram_history),
        "timestamp": datetime.now(TZ).isoformat(),
    }


@lru_cache()
def check_connectivity():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect(("1.1.1.1", 53))
        sock.close()
        return "online"
    except Exception:
        return "offline"


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    stats = get_system_stats()
    conn = check_connectivity()
    template = jinja_env.get_template("index.html")
    html = template.render(stats=stats, connectivity=conn, request=request, title=DASHBOARD_TITLE)
    return HTMLResponse(html)


@app.get("/api/stats")
async def api_stats():
    return get_system_stats()


@app.get("/api/ping")
async def api_ping():
    return {"status": check_connectivity()}


@app.get("/api/cpu")
async def api_cpu():
    stats = get_system_stats()
    return {"cpu": stats["cpu"], "history": stats["cpu_history"]}


@app.get("/api/ram")
async def api_ram():
    stats = get_system_stats()
    return {"ram_percent": stats["ram_percent"], "history": stats["ram_history"]}


@app.get("/api/alerts")
async def api_alerts():
    return {"alerts": alerts}


@app.get("/fragments/stats", response_class=HTMLResponse)
async def fragment_stats(request: Request):
    stats = get_system_stats()
    template = jinja_env.get_template("fragments/stats.html")
    html = template.render(stats=stats)
    return HTMLResponse(html)


@app.get("/fragments/connectivity", response_class=HTMLResponse)
async def fragment_connectivity(request: Request):
    conn = check_connectivity()
    template = jinja_env.get_template("fragments/connectivity.html")
    html = template.render(connectivity=conn)
    return HTMLResponse(html)


@app.get("/health")
async def health():
    return {"status": "ok"}