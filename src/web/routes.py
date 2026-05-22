"""Web UI routes for the AI Food Analyzer.

Serves a simple single-page application that allows users to upload
a meal photo and view the analysis results.
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

router = APIRouter(tags=["web"])

HERE = Path(__file__).parent
TEMPLATES = HERE / "templates"
STATIC = HERE / "static"

INDEX_HTML = TEMPLATES / "index.html"


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index():
    """Serve the main web page."""
    if INDEX_HTML.exists():
        return INDEX_HTML.read_text(encoding="utf-8")
    return HTMLResponse("<h1>AI Food Analyzer</h1><p>Frontend not built yet.</p>")


def mount_static(app):
    """Mount static files if the directory exists."""
    if STATIC.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
