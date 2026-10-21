"""SaveFlow MCP tools. Run locally: python -m server.mcp_server"""
from __future__ import annotations
from mcp.server.fastmcp import FastMCP
from .downloader import download_video as do_download
from .downloader import inspect_video as do_inspect
from .downloader import supported_platforms as do_supported
from .processor import (media_info as do_media_info, process_video as do_process,
                        create_thumbnail as do_thumbnail, extract_audio as do_audio,
                        split_clips as do_clips, sha256_media as do_hash)

from .instagram import inspect_instagram_reel as do_instagram, normalize_reel_url as do_normalize

mcp = FastMCP("SaveFlow | Video Studio")

@mcp.tool()
def inspect_video(url: str) -> dict:
    """Inspect a public social-video URL for title, creator, duration and available resolutions; no download."""
    return do_inspect(url)

@mcp.tool()
def inspect_instagram_reel(url: str, provider: str = "auto") -> dict:
    """Scrape metadata for one PUBLIC Instagram Reel. Auto: yt-dlp then optional Apify (SAVEFLOW_APIFY_TOKEN). Supports /reel/ and /reels/ links. Apify can incur charges. Temporary CDN URLs are not local video files."""
    return do_instagram(url, provider)

@mcp.tool()
def normalize_instagram_reel_link(url: str) -> dict:
    """Normalize Instagram reel link variants and strip share tracking before inspection."""
    return {"canonical_url": do_normalize(url)}

@mcp.tool()
def download_video(url: str, quality: str = "best", audio_only: bool = False) -> dict:
    """Download authorized public video in best quality. Returns LOCAL filepath, not a hosted URL."""
    return do_download(url, quality, audio_only)

@mcp.tool()
def supported_platforms() -> dict:
    """Accepted domains; availability of media tools (FFmpeg and optional AI upscale)."""
    import shutil
    result = do_supported()
    result.update({"ffprobe_available": bool(shutil.which("ffprobe")),
                   "ai_upscaler_available": bool(shutil.which("realesrgan-ncnn-vulkan")),
                   "social_presets": ["original", "reels", "shorts", "tiktok", "story", "square", "feed", "landscape"]})
    return result

@mcp.tool()
def analyze_local_video(path: str) -> dict:
    """Inspect a previously downloaded or imported video for aspect ratio, codecs, FPS and tag keys."""
    return do_media_info(path)

@mcp.tool()
def process_video(path: str, preset: str = "reels", upscale: str = "none",
                  framing: str = "blur", fps: str = "source", audio: str = "normalize",
                  start: float = 0, end: float | None = None, crf: int = 19,
                  clean_metadata: bool = True) -> dict:
    """Export locally: social presets, 2x/4x Lanczos or optional AI upscaling, metadata cleaning, sound normalization, cropping, padding, blur and clips. Does not guarantee virality."""
    return do_process(path, preset, upscale, framing, fps, audio, start, end, crf, clean_metadata)

@mcp.tool()
def download_and_process(url: str, quality: str = "best", preset: str = "reels",
                         upscale: str = "none", framing: str = "blur",
                         audio: str = "normalize") -> dict:
    """One-step public video download plus clean, ready-to-publish social video export; returns LOCAL paths."""
    original = do_download(url, quality)
    result = do_process(original["path"], preset=preset, upscale=upscale,
                        framing=framing, audio=audio)
    return {"original": original, "export": result}

@mcp.tool()
def create_thumbnail(path: str, at_seconds: float = 1.0, width: int = 1080) -> dict:
    """Extract a clean JPEG cover frame for a social post."""
    return do_thumbnail(path, at_seconds, width)

@mcp.tool()
def extract_audio(path: str, format: str = "mp3") -> dict:
    """Extract audio as MP3, M4A, or WAV from a local saved video."""
    return do_audio(path, format)

@mcp.tool()
def split_video_into_clips(path: str, segment_seconds: int = 30,
                           max_clips: int = 8, preset: str = "reels") -> dict:
    """Split authorized footage into equal-length clips for short-form editing; not AI-selected highlights."""
    return do_clips(path, segment_seconds, max_clips, preset)

@mcp.tool()
def verify_video_hash(path: str) -> dict:
    """Compute SHA-256 checksum of the media for integrity and duplicate management."""
    return do_hash(path)

if __name__ == "__main__":
    mcp.run(transport="stdio")
