
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import psutil
import platform
import shutil

app = FastAPI(title="LaptopCare AI")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.get("/api/health")
def laptop_health():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = shutil.disk_usage("/")

    warnings = []

    if cpu > 80:
        warnings.append("High CPU usage detected")

    if memory.percent > 80:
        warnings.append("High memory usage detected")

    disk_percent = (disk.used / disk.total) * 100

    if disk_percent > 85:
        warnings.append("Low disk space available")

    return {
        "device": platform.node(),
        "operating_system": platform.system(),
        "cpu_usage": cpu,
        "memory_usage": memory.percent,
        "memory_total_gb": round(memory.total / (1024 ** 3), 2),
        "disk_usage": round((disk.used / disk.total) * 100, 2),
        "disk_free_gb": round(disk.free / (1024 ** 3), 2),
        "status": "Warning" if warnings else "Healthy",
        "warnings": warnings
    }
