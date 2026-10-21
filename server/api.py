"""Optional authenticated HTTP backend.

POST /api/download -> job ID; GET /api/jobs/{id} -> status / signed file URL.
Use a reverse proxy with HTTPS and rate limits for production deployment.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
import secrets
import time
from concurrent.futures import ThreadPoolExecutor
from threading import RLock
from fastapi import FastAPI, Header, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from .downloader import DownloadError, download_video, inspect_video, BASE_DIR, MAX_BYTES
from .processor import process_video, media_info

app = FastAPI(title="SaveFlow — Social Video Saver", docs_url=None, redoc_url=None)
EXECUTOR = ThreadPoolExecutor(max_workers=2)
JOBS: dict[str, dict] = {}
LOCK = RLock()
MAX_PENDING = 8
JOB_TTL = 3600

class DownloadRequest(BaseModel):
    url: str = Field(min_length=10, max_length=2048)
    quality: str = "best"
    audio_only: bool = False

class ProcessRequest(BaseModel):
    path: str = Field(min_length=1, max_length=4096)
    preset: str = "reels"
    upscale: str = "none"
    framing: str = "blur"
    fps: str = "source"
    audio: str = "normalize"
    start: float = 0
    end: float | None = None
    crf: int = 19
    clean_metadata: bool = True

class DownloadAndProcessRequest(BaseModel):
    url: str = Field(min_length=10, max_length=2048)
    quality: str = "best"
    preset: str = "reels"
    upscale: str = "none"
    framing: str = "blur"
    audio: str = "normalize"

def require_auth(authorization: str | None) -> None:
    token = os.getenv("SAVEFLOW_API_TOKEN", "")
    if len(token) < 24:
        raise HTTPException(status_code=503, detail="API not configured: set a long SAVEFLOW_API_TOKEN")
    supplied = authorization.removeprefix("Bearer ") if authorization else ""
    if not hmac.compare_digest(supplied, token):
        raise HTTPException(status_code=401, detail="Bearer token required")

def _verify_token(authorization: str | None = Header(default=None)) -> None:
    require_auth(authorization)

def _cleanup() -> None:
    now = time.time()
    with LOCK:
        old = [key for key, value in JOBS.items() if now - value["created"] > JOB_TTL and value["status"] != "running"]
        for key in old:
            record = JOBS.pop(key)
            if record.get("result"):
                from pathlib import Path
                import shutil
                for pth in (record["result"].get("path"), record["result"].get("source_path")):
                    if not pth:
                        continue
                    file_path = Path(pth).resolve()
                    if file_path.is_file() and file_path.parent.is_relative_to(BASE_DIR.resolve()):
                        shutil.rmtree(file_path.parent, ignore_errors=True)

def _sign(job: str, exp: int) -> str:
    payload = f"{job}:{exp}".encode()
    secret = os.environ.get("SAVEFLOW_API_TOKEN", "").encode()
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()

def _run_job(job: str, request: DownloadRequest) -> None:
    with LOCK:
        JOBS[job]["status"] = "running"
    try:
        result = download_video(request.url, request.quality, request.audio_only)
        with LOCK:
            JOBS[job].update(status="completed", result=result)
    except Exception as exc:
        with LOCK:
            JOBS[job].update(status="failed", error=str(exc)[:500])


def _run_process(job: str, request: ProcessRequest) -> None:
    with LOCK:
        JOBS[job]["status"] = "running"
    try:
        result = process_video(request.path, request.preset, request.upscale, request.framing,
                               request.fps, request.audio, request.start, request.end,
                               request.crf, request.clean_metadata)
        with LOCK:
            JOBS[job].update(status="completed", result=result)
    except Exception as exc:
        with LOCK:
            JOBS[job].update(status="failed", error=str(exc)[:500])


def _run_download_process(job: str, request: DownloadAndProcessRequest) -> None:
    with LOCK:
        JOBS[job]["status"] = "running"
    original = None
    try:
        original = download_video(request.url, request.quality)
        result = process_video(original["path"], preset=request.preset, upscale=request.upscale,
                               framing=request.framing, audio=request.audio)
        result["source_path"] = original["path"]
        with LOCK:
            JOBS[job].update(status="completed", result=result)
    except Exception as exc:
        if original:
            import shutil
            from pathlib import Path
            shutil.rmtree(Path(original["path"]).parent, ignore_errors=True)
        with LOCK:
            JOBS[job].update(status="failed", error=str(exc)[:500])


def _new_job() -> str:
    _cleanup()
    with LOCK:
        active = sum(value["status"] in ("queued", "running") for value in JOBS.values())
        if active >= MAX_PENDING:
            raise HTTPException(status_code=429, detail="Queue is full")
        job = secrets.token_hex(16)
        JOBS[job] = {"status": "queued", "created": time.time()}
        return job

@app.get("/health")
def health():
    return {"status": "ok", "service": "SaveFlow", "mode": "self-hosted"}

@app.post("/api/download", status_code=202)
def create_download(data: DownloadRequest, authorization: str | None = Header(default=None)):
    require_auth(authorization)
    from .downloader import validate_url
    try:
        validate_url(data.url)
        if data.quality not in {"best", "2160p", "1440p", "1080p", "720p", "480p", "360p"}:
            raise DownloadError("Invalid quality")
    except DownloadError as ex:
        raise HTTPException(status_code=400, detail=str(ex)) from ex
    job = _new_job()
    EXECUTOR.submit(_run_job, job, data)
    return {"job_id": job, "status": "queued", "status_path": f"/api/jobs/{job}"}

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str, authorization: str | None = Header(default=None)):
    require_auth(authorization)
    _cleanup()
    with LOCK:
        record = JOBS.get(job_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Unknown or expired job")
        result = dict(record)
    response = {"job_id": job_id, "status": result["status"]}
    if result.get("error"):
        response["error"] = result["error"]
    if result.get("result"):
        media = result["result"]
        expires = int(time.time()) + 600
        sig = _sign(job_id, expires)
        public_url = os.getenv("SAVEFLOW_PUBLIC_URL", "").rstrip("/")
        path = f"/api/files/{job_id}?expires={expires}&signature={sig}"
        response.update({"filename": media["filename"], "size_bytes": media["size_bytes"],
                         "download_url": public_url + path if public_url else None,
                         "download_path": path, "expires_in_seconds": 600})
    return response

@app.get("/api/files/{job_id}")
def get_file(job_id: str, expires: int = Query(...), signature: str = Query(...)):
    _cleanup()
    if expires < time.time() or expires > time.time() + 660 or not hmac.compare_digest(signature, _sign(job_id, expires)):
        raise HTTPException(status_code=403, detail="Invalid or expired link")
    from pathlib import Path
    with LOCK:
        job = JOBS.get(job_id)
        if not job or job["status"] != "completed":
            raise HTTPException(status_code=404, detail="File not found")
        media = job["result"]
    path = Path(media["path"]).resolve()
    if not path.parent.is_relative_to(BASE_DIR.resolve()) or not path.is_file():
        raise HTTPException(status_code=404, detail="File no longer available")
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


@app.post("/api/process", status_code=202)
def create_process(data: ProcessRequest, authorization: str | None = Header(default=None)):
    require_auth(authorization)
    try:
        media_info(data.path)  # reject unapproved paths before queuing
    except (DownloadError, ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if data.preset not in {"original", "reels", "shorts", "tiktok", "story", "square", "feed", "landscape"}:
        raise HTTPException(status_code=400, detail="Invalid preset")
    job = _new_job()
    EXECUTOR.submit(_run_process, job, data)
    return {"job_id": job, "status": "queued", "status_path": f"/api/jobs/{job}"}


@app.post("/api/download-and-process", status_code=202)
def create_download_and_process(data: DownloadAndProcessRequest,
                                authorization: str | None = Header(default=None)):
    require_auth(authorization)
    from .downloader import validate_url
    from .processor import UPSCALE_MODES, PRESETS, FRAMING, AUDIO_MODES
    try:
        validate_url(data.url)
        if data.quality not in {"best", "2160p", "1440p", "1080p", "720p", "480p", "360p"}:
            raise DownloadError("Invalid quality")
        if data.upscale not in UPSCALE_MODES or data.preset not in PRESETS:
            raise DownloadError("Invalid upscale or preset")
        if data.framing not in FRAMING or data.audio not in AUDIO_MODES:
            raise DownloadError("Invalid framing or audio option")
    except DownloadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    job = _new_job()
    EXECUTOR.submit(_run_download_process, job, data)
    return {"job_id": job, "status": "queued", "status_path": f"/api/jobs/{job}"}


@app.post("/api/upload", status_code=201)
async def create_upload(file: UploadFile = File(...), authorization: str | None = Header(default=None)):
    require_auth(authorization)
    from pathlib import Path
    import shutil
    extension = Path(file.filename or "").suffix.lower()
    if extension not in {".mp4", ".mkv", ".mov", ".m4v", ".webm", ".avi"}:
        raise HTTPException(status_code=400, detail="Unsupported extension")
    max_upload = min(MAX_BYTES, int(os.getenv("SAVEFLOW_UPLOAD_MAX_BYTES", str(200 * 1024 * 1024))))
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    directory = BASE_DIR / secrets.token_hex(12)
    directory.mkdir(mode=0o700)
    target = directory / ("upload" + extension)
    size = 0
    try:
        with target.open("xb") as sink:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > max_upload:
                    raise HTTPException(status_code=413, detail="Upload too large")
                sink.write(chunk)
        info = media_info(str(target))
        return {"path": str(target), "info": info,
                "note": "Use returned path with POST /api/process. Requires bearer token."}
    except HTTPException:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    except (DownloadError, ValueError, FileNotFoundError) as exc:
        shutil.rmtree(directory, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await file.close()


class ReelInspectRequest(BaseModel):
    url: str = Field(min_length=30, max_length=2048)
    provider: str = "auto"

@app.post("/api/reel/inspect")
def api_inspect_reel(data: ReelInspectRequest, authorization: str | None = Header(default=None)):
    """Inspect one public Reel. Optional Apify token is server-side only."""
    require_auth(authorization)
    from .instagram import inspect_instagram_reel
    try:
        return inspect_instagram_reel(data.url, data.provider)
    except DownloadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/", include_in_schema=False)
def studio_home():
    """Self-hosted dashboard; media operations are always authenticated."""
    from pathlib import Path
    html = Path(__file__).resolve().parent.parent / "web" / "index.html"
    return FileResponse(html, media_type="text/html", headers={"Cache-Control": "no-store"})


@app.get("/favicon.png", include_in_schema=False)
def studio_icon():
    from pathlib import Path
    icon = Path(__file__).resolve().parent.parent / "assets" / "icon.svg"
    return FileResponse(icon, media_type="image/svg+xml")


# Register stateless remote MCP alongside the existing authenticated REST API.
from .remote_mcp import router as remote_mcp_router
app.include_router(remote_mcp_router)
