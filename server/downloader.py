"""Safe, bounded yt-dlp downloader for public social-media links.

Requires ffmpeg on PATH for highest-quality video+audio merging.
No cookies, logins, DRM decryption or private content access are supported.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

MAX_BYTES = int(os.getenv("SAVEFLOW_MAX_BYTES", str(2 * 1024**3)))
MAX_SECONDS = int(os.getenv("SAVEFLOW_TIMEOUT_SECONDS", "1200"))
BASE_DIR = Path(os.getenv("SAVEFLOW_OUTPUT_DIR", str(Path.home() / "Downloads" / "SaveFlow"))).expanduser().resolve()
DOMAINS = {
    "youtube.com", "youtu.be", "youtube-nocookie.com", "tiktok.com",
    "instagram.com", "twitter.com", "x.com", "reddit.com", "redd.it",
    "facebook.com", "fb.watch", "threads.net", "vimeo.com", "dailymotion.com",
    "twitch.tv", "clips.twitch.tv", "pinterest.com", "pin.it",
    "soundcloud.com", "bsky.app", "kick.com", "rumble.com",
    "streamable.com", "imgur.com", "tumblr.com", "linkedin.com",
    "bilibili.com", "douyin.com", "snapchat.com", "vk.com", "ok.ru",
    "bandcamp.com", "mixcloud.com", "ted.com", "9gag.com",
    "weibo.com", "xiaohongshu.com", "rednote.com", "loom.com",
}

class DownloadError(RuntimeError):
    """A link could not be inspected or downloaded."""


def validate_url(url: str) -> str:
    if not isinstance(url, str) or len(url) > 2048 or not url.startswith(("https://", "http://")):
        raise DownloadError("Use a full https:// or http:// social video URL.")
    try:
        p = urlsplit(url)
        host = (p.hostname or "").lower().rstrip(".")
        _ = p.port  # Reject malformed ports
    except ValueError as ex:
        raise DownloadError("Invalid URL.") from ex
    if p.username or p.password or p.port not in (None, 80, 443):
        raise DownloadError("User info and nonstandard ports are not allowed.")
    if not host or not any(host == d or host.endswith("." + d) for d in DOMAINS):
        raise DownloadError("This domain is not on the supported social-platform allowlist.")
    if p.scheme != "https":
        raise DownloadError("Only HTTPS links are accepted to reduce transport risks.")
    # Instagram presents equivalent /reels/ and /reel/ paths, often with share tracking.
    # Canonicalize without touching other platforms or fetching user-supplied hosts.
    if host in {"instagram.com", "www.instagram.com", "m.instagram.com"}:
        match = re.match(r"^/(?:reels|reel)/([A-Za-z0-9_-]{5,32})(?:/|$)", p.path)
        if match:
            return f"https://www.instagram.com/reel/{match.group(1)}/"
    return url


def _run(args: list[str], timeout: int) -> str:
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--ignore-config", "--no-playlist", "--no-warnings", *args],
            check=False, capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
    except FileNotFoundError as exc:
        raise DownloadError("Python or yt-dlp is missing. Install with pip install -e .") from exc
    except subprocess.TimeoutExpired as exc:
        raise DownloadError(f"Download timed out after {timeout} seconds.") from exc
    if completed.returncode:
        message = (completed.stderr or completed.stdout).strip()
        # Never forward arbitrary giant tool logs
        raise DownloadError((message[-1200:] or "Unable to process this link."))
    return completed.stdout


def inspect_video(url: str) -> dict:
    url = validate_url(url)
    raw = _run(["--dump-single-json", "--skip-download", "--no-progress", url], 75)
    try:
        info = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DownloadError("Could not parse video metadata.") from exc
    if info.get("_type") == "playlist":
        raise DownloadError("Playlists are not supported: provide a single video URL.")
    formats = info.get("formats", [])
    video_formats = [f for f in formats if f.get("vcodec") not in (None, "none")]
    resolutions = sorted({int(f["height"]) for f in video_formats if isinstance(f.get("height"), int)}, reverse=True)
    return {
        "title": info.get("title"), "creator": info.get("uploader") or info.get("channel"),
        "site": info.get("extractor_key"), "duration_seconds": info.get("duration"),
        "thumbnail": info.get("thumbnail"), "source_url": url,
        "available_heights": resolutions[:16], "max_height": resolutions[0] if resolutions else None,
        "is_live": bool(info.get("is_live")),
        "note": "Formats and availability depend on the source and may change.",
    }


def download_video(url: str, quality: str = "best", audio_only: bool = False) -> dict:
    url = validate_url(url)
    allowed = {"best", "2160p", "1440p", "1080p", "720p", "480p", "360p"}
    if quality not in allowed:
        raise DownloadError("quality must be best, 2160p, 1440p, 1080p, 720p, 480p or 360p.")
    if not shutil.which("ffmpeg") and not audio_only:
        raise DownloadError("ffmpeg is required for merging the best video and audio streams.")

    job_id = secrets.token_hex(12)
    directory = BASE_DIR / job_id
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    prefix = directory / "video"
    max_mib = max(1, MAX_BYTES // (1024 * 1024))
    args = [
        "--no-progress", "--no-overwrites", "--no-mtime", "--max-downloads", "1",
        "--max-filesize", f"{max_mib}M", "--output", str(prefix) + ".%(ext)s",
        "--print", "after_move:filepath",
    ]
    if audio_only:
        args += ["--format", "bestaudio/best", "--extract-audio", "--audio-format", "best"]
    else:
        selector = "bv*+ba/b"
        if quality != "best":
            height = int(quality[:-1])
            selector = f"bv*[height<={height}]+ba/b[height<={height}]/b"
        args += ["--format", selector, "--merge-output-format", "mp4/mkv"]
    try:
        output = _run([*args, url], MAX_SECONDS)
        listed = [line.strip() for line in output.splitlines() if line.strip()]
        paths = [Path(line) for line in listed if line.startswith(str(directory) + os.sep)]
        files = [p for p in directory.iterdir() if p.is_file() and not p.name.endswith((".part", ".ytdl", ".temp"))]
        media = next((p for p in reversed(paths) if p.is_file()), None)
        if media is None and len(files) == 1:
            media = files[0]
        if media is None:
            raise DownloadError("Downloader finished without producing one playable media file.")
        media = media.resolve()
        if not media.is_relative_to(directory.resolve()):
            raise DownloadError("Unsafe output path.")
        size = media.stat().st_size
        if size > MAX_BYTES:
            raise DownloadError("Output exceeds configured file size limit.")
        return {
            "status": "completed", "job_id": job_id, "path": str(media),
            "filename": media.name, "size_bytes": size, "quality": quality,
            "audio_only": audio_only, "source_url": url,
            "note": "Local file is ready. Attach it using your host's file support or download it from the optional API.",
        }
    except Exception:
        shutil.rmtree(directory, ignore_errors=True)
        raise


def supported_platforms() -> dict:
    return {"platform_domains": sorted(DOMAINS), "engine": "yt-dlp", "ffmpeg_available": bool(shutil.which("ffmpeg"))}
