"""Local, bounded FFmpeg processor for videos the user is authorized to edit.

No watermark-removal or fingerprint-evasion features. Metadata-clean means
removing optional descriptive tags, not guaranteeing content anonymity.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import secrets
import shutil
import subprocess
import tempfile
from pathlib import Path

from .downloader import BASE_DIR, MAX_BYTES, DownloadError

PROCESS_TIMEOUT = int(os.getenv("SAVEFLOW_PROCESS_TIMEOUT", "1800"))
AI_MAX_DURATION = int(os.getenv("SAVEFLOW_AI_MAX_SECONDS", "90"))
MAX_INPUT_DURATION = int(os.getenv("SAVEFLOW_MAX_DURATION", "3600"))
MAX_PIXELS = int(os.getenv("SAVEFLOW_MAX_PIXELS", str(3840 * 3840)))
PRESETS = {
    "original": None,
    "reels": (1080, 1920),
    "shorts": (1080, 1920),
    "tiktok": (1080, 1920),
    "story": (1080, 1920),
    "square": (1080, 1080),
    "feed": (1080, 1350),
    "landscape": (1920, 1080),
}
AUDIO_MODES = {"original", "normalize", "mute"}
FRAMING = {"crop", "pad", "blur"}
UPSCALE_MODES = {"none", "2x", "4x", "ai2x", "ai4x"}


def _run(args: list[str], timeout: int = PROCESS_TIMEOUT) -> str:
    try:
        result = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=timeout, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise DownloadError(f"Media tool unavailable or exceeded {timeout}s.") from exc
    if result.returncode:
        raise DownloadError((result.stderr or result.stdout)[-1200:] or "Media processing failed.")
    return result.stdout


def _safe_path(filename: str) -> Path:
    if not isinstance(filename, str) or not filename:
        raise DownloadError("Supply an existing local media path.")
    path = Path(filename).expanduser().resolve(strict=True)
    allowed_roots = [BASE_DIR.resolve()]
    upload_dir = os.getenv("SAVEFLOW_IMPORT_DIR", "")
    if upload_dir:
        allowed_roots.append(Path(upload_dir).expanduser().resolve())
    if not path.is_file() or not any(path.is_relative_to(root) for root in allowed_roots):
        raise DownloadError("Media must be inside SAVEFLOW_OUTPUT_DIR or explicitly configured SAVEFLOW_IMPORT_DIR.")
    if path.stat().st_size > MAX_BYTES:
        raise DownloadError("Media exceeds configured input size limit.")
    if path.suffix.lower() not in {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}:
        raise DownloadError("File type is not a supported video container.")
    return path


def media_info(filename: str) -> dict:
    """Inspect codec, dimensions, tags, duration and useful export details."""
    path = _safe_path(filename)
    raw = _run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)], 30)
    try:
        data = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise DownloadError("Invalid ffprobe response.") from exc
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not video:
        raise DownloadError("No video stream in this file.")
    try:
        duration = float(data.get("format", {}).get("duration") or video.get("duration") or 0)
        width, height = int(video["width"]), int(video["height"])
    except (ValueError, TypeError, KeyError) as exc:
        raise DownloadError("Could not read video dimensions or duration.") from exc
    if not math.isfinite(duration) or duration <= 0 or duration > MAX_INPUT_DURATION:
        raise DownloadError("Invalid or over-limit video duration.")
    if width <= 0 or height <= 0 or width * height > MAX_PIXELS:
        raise DownloadError("Input dimensions exceed configured pixel safety limit.")
    fps_str = video.get("avg_frame_rate") or "0/1"
    try:
        from fractions import Fraction
        fps = float(Fraction(fps_str))
    except (ValueError, ZeroDivisionError):
        fps = 0.0
    all_tags = dict(data.get("format", {}).get("tags") or {})
    for stream in data.get("streams", []):
        all_tags.update(stream.get("tags") or {})
    return {"path": str(path), "filename": path.name, "size_bytes": path.stat().st_size,
            "width": width, "height": height, "fps": round(fps, 4), "duration_seconds": round(duration, 3),
            "video_codec": video.get("codec_name"), "audio_codec": audio.get("codec_name") if audio else None,
            "has_audio": bool(audio), "tag_keys": sorted(all_tags),
            "note": "Container/codec fields such as encoder may still exist after metadata cleaning."}


def _target_dims(info: dict, preset: str, upscale: str) -> tuple[int, int]:
    if preset not in PRESETS:
        raise DownloadError("Invalid preset. Use original, reels, shorts, tiktok, story, square, feed, landscape.")
    if upscale not in UPSCALE_MODES:
        raise DownloadError("Invalid upscale. Use none, 2x, 4x, ai2x or ai4x.")
    w, h = PRESETS[preset] or (info["width"], info["height"])
    multiplier = (4 if "4x" in upscale else 2 if "2x" in upscale else 1)
    w, h = w * multiplier, h * multiplier
    if w * h > MAX_PIXELS or w > 3840 or h > 3840:
        raise DownloadError("Target is too large; choose 2x or a smaller preset.")
    # H.264 yuv420p needs even dimensions.
    return w + w % 2, h + h % 2


def _filter(target: tuple[int, int], framing: str, fps: str,
            source: dict, ai_scaled: bool = False) -> str:
    if framing not in FRAMING:
        raise DownloadError("framing must be crop, pad or blur.")
    w, h = target
    if framing == "crop":
        f = f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h}"
    elif framing == "pad":
        f = (f"scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos,"
             f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black")
    else:
        f = (f"split=2[fg][bg];[bg]scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,"
             f"crop={w}:{h},boxblur=20:2[bg2];"
             f"[fg]scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos[fg2];"
             f"[bg2][fg2]overlay=(W-w)/2:(H-h)/2")
    if fps != "source":
        if fps not in {"30", "60"}:
            raise DownloadError("fps must be source, 30 or 60.")
        f += f",fps={fps}"
    # AI upscale already enhances full frames; ordinary Lanczos only resizes.
    return f


def _clip_window(info: dict, start: float, end: float | None) -> tuple[float, float]:
    if not isinstance(start, (int, float)) or not math.isfinite(start) or start < 0:
        raise DownloadError("start must be a non-negative finite number.")
    duration = info["duration_seconds"]
    if end is None:
        end = duration
    if not isinstance(end, (int, float)) or not math.isfinite(end) or end <= start or end > duration + .1:
        raise DownloadError("end must be later than start and no later than media duration.")
    if end - start < 0.3:
        raise DownloadError("Clips shorter than 0.3 seconds are not supported.")
    return float(start), float(end)


def _new_output(stem: str = "ready") -> Path:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    output_dir = BASE_DIR / secrets.token_hex(12)
    output_dir.mkdir(mode=0o700)
    return output_dir / stem


def _ai_frames(path: Path, destination: Path, info: dict, scale: int,
               start: float, end: float) -> Path:
    """Real-ESRGAN Vulkan upscale, opt-in, bounded to short CFR clips."""
    engine = shutil.which("realesrgan-ncnn-vulkan")
    if engine is None:
        raise DownloadError("AI upscale requires realesrgan-ncnn-vulkan installed on the video worker; use native 2x otherwise.")
    if end - start > AI_MAX_DURATION:
        raise DownloadError(f"AI upscaling is capped at {AI_MAX_DURATION}s; trim the clip first.")
    fps = info["fps"]
    if not 1 <= fps <= 60:
        raise DownloadError("AI upscale requires a readable frame rate between 1 and 60 fps.")
    max_frames = int(os.getenv("SAVEFLOW_AI_MAX_FRAMES", "600"))
    if fps * (end - start) > max_frames:
        raise DownloadError(f"AI upscale over frame budget of {max_frames}; trim your clip.")
    frames_in = destination / "frames_in"
    frames_out = destination / "frames_out"
    frames_in.mkdir()
    frames_out.mkdir()
    _run(["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y", "-ss", str(start),
          "-i", str(path), "-t", str(end - start), "-vsync", "0", str(frames_in / "%08d.png")])
    if not any(frames_in.iterdir()):
        raise DownloadError("No frames decoded for AI upscale.")
    _run([engine, "-i", str(frames_in), "-o", str(frames_out),
          "-s", str(scale), "-n", "realesrgan-x4plus", "-f", "png"], PROCESS_TIMEOUT)
    if len(list(frames_out.glob("*.png"))) != len(list(frames_in.glob("*.png"))):
        raise DownloadError("AI upscaler returned incomplete frame sequence.")
    # VFR timing approximation; the tool reports this limitation to users.
    intermediate = destination / "ai_video.mkv"
    _run(["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y", "-framerate", str(fps),
          "-i", str(frames_out / "%08d.png"), "-c:v", "ffv1", str(intermediate)])
    shutil.rmtree(frames_in, ignore_errors=True)
    shutil.rmtree(frames_out, ignore_errors=True)
    return intermediate


def process_video(filename: str, preset: str = "reels", upscale: str = "none",
                  framing: str = "blur", fps: str = "source", audio: str = "normalize",
                  start: float = 0, end: float | None = None, crf: int = 19,
                  clean_metadata: bool = True) -> dict:
    """Export video in a social-friendly format; never claims content becomes 'new'."""
    path = _safe_path(filename)
    info = media_info(str(path))
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise DownloadError("FFmpeg and FFprobe must be installed on the video worker.")
    if audio not in AUDIO_MODES or framing not in FRAMING or fps not in {"source", "30", "60"}:
        raise DownloadError("Invalid audio, framing or fps option.")
    if not isinstance(crf, int) or not 15 <= crf <= 30:
        raise DownloadError("CRF must be an integer from 15 to 30 (lower = larger/better).")
    s, e = _clip_window(info, start, end)
    target = _target_dims(info, preset, upscale)
    out_base = _new_output("saveflow")
    folder = out_base.parent
    destination = out_base.with_suffix(".mp4")
    ai_source = None
    try:
        source = path
        if upscale.startswith("ai"):
            ai_source = _ai_frames(path, folder, info, int(upscale[2]), s, e)
            source = ai_source
        filt = _filter(target, framing, fps, info)
        # Blur framing creates a complex graph; output must explicitly map its last label.
        cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y"]
        if not ai_source:
            cmd += ["-ss", str(s), "-i", str(source), "-t", str(e - s)]
            audio_input = 0
        else:
            cmd += ["-i", str(ai_source), "-ss", str(s), "-i", str(path), "-t", str(e - s)]
            audio_input = 1
        if framing == "blur":
            # Explicitly label the final overlay stream for -filter_complex.
            cmd += ["-filter_complex", "[0:v]" + filt + "[vout]", "-map", "[vout]"]
        else:
            cmd += ["-vf", filt, "-map", "0:v:0"]
        if audio != "mute" and info["has_audio"]:
            cmd += ["-map", f"{audio_input}:a:0?"]
        cmd += ["-map_metadata", "-1" if clean_metadata else "0", "-map_chapters", "-1"]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-max_muxing_queue_size", "1024"]
        if audio == "mute" or not info["has_audio"]:
            cmd += ["-an"]
        else:
            if audio == "normalize":
                cmd += ["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"]
            cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
        if clean_metadata:
            cmd += ["-metadata", "title=", "-metadata", "comment=", "-metadata", "description=",
                    "-metadata:s:v:0", "title=", "-metadata:s:a:0", "title="]
        cmd += [str(destination)]
        _run(cmd)
        if not destination.is_file() or destination.stat().st_size == 0:
            raise DownloadError("Video export did not produce an output file.")
        if destination.stat().st_size > MAX_BYTES:
            raise DownloadError("Export exceeds configured file size limit.")
        out_info = media_info(str(destination))
        return {"status": "completed", "path": str(destination), "filename": destination.name,
                "size_bytes": destination.stat().st_size, "preset": preset, "upscale": upscale,
                "width": out_info["width"], "height": out_info["height"],
                "duration_seconds": out_info["duration_seconds"], "clean_metadata": clean_metadata,
                "audio": audio, "framing": framing,
                "notes": ["Metadata tags are minimized; no promise of removing embedded identifiers or platform fingerprints.",
                          "Native scaling is interpolation; AI restoration requires optional Real-ESRGAN runtime.",
                          "Social export cannot guarantee distribution, monetization or virality."]}
    except Exception:
        shutil.rmtree(folder, ignore_errors=True)
        raise
    finally:
        if ai_source and ai_source.exists():
            ai_source.unlink()


def create_thumbnail(filename: str, at_seconds: float = 1.0, width: int = 1080) -> dict:
    path = _safe_path(filename)
    info = media_info(filename)
    if not isinstance(width, int) or not 320 <= width <= 1920:
        raise DownloadError("Thumbnail width must be between 320 and 1920.")
    if not isinstance(at_seconds, (int, float)) or not math.isfinite(at_seconds) or at_seconds < 0 or at_seconds >= info["duration_seconds"]:
        raise DownloadError("Timestamp must be inside video duration.")
    output = _new_output("cover").with_suffix(".jpg")
    try:
        _run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(at_seconds),
              "-i", str(path), "-frames:v", "1", "-vf", f"scale={width}:-2:flags=lanczos",
              "-map_metadata", "-1", "-q:v", "2", str(output)], 60)
        if not output.exists():
            raise DownloadError("Unable to generate thumbnail.")
        return {"path": str(output), "filename": output.name, "size_bytes": output.stat().st_size}
    except Exception:
        shutil.rmtree(output.parent, ignore_errors=True)
        raise


def extract_audio(filename: str, format: str = "mp3") -> dict:
    path = _safe_path(filename)
    info = media_info(filename)
    if not info["has_audio"]:
        raise DownloadError("Video has no audio stream.")
    if format not in {"mp3", "m4a", "wav"}:
        raise DownloadError("Audio output must be mp3, m4a or wav.")
    output = _new_output("audio").with_suffix("." + format)
    try:
        codec = {"mp3": ["-c:a", "libmp3lame", "-b:a", "192k"],
                 "m4a": ["-c:a", "aac", "-b:a", "192k"],
                 "wav": ["-c:a", "pcm_s16le"]}[format]
        _run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path),
              "-vn", "-map", "0:a:0", "-map_metadata", "-1", "-map_chapters", "-1", *codec, str(output)])
        if not output.exists():
            raise DownloadError("Audio extraction failed.")
        return {"path": str(output), "filename": output.name, "size_bytes": output.stat().st_size}
    except Exception:
        shutil.rmtree(output.parent, ignore_errors=True)
        raise


def split_clips(filename: str, segment_seconds: int = 30, max_clips: int = 8,
                preset: str = "reels") -> dict:
    info = media_info(filename)
    if not isinstance(segment_seconds, int) or segment_seconds < 5 or segment_seconds > 120:
        raise DownloadError("segment_seconds must be between 5 and 120.")
    if not isinstance(max_clips, int) or not 1 <= max_clips <= 12:
        raise DownloadError("max_clips must be between 1 and 12.")
    count = min(max_clips, math.ceil(info["duration_seconds"] / segment_seconds))
    results = []
    for i in range(count):
        start = i * segment_seconds
        end = min(info["duration_seconds"], (i + 1) * segment_seconds)
        if end - start < .3:
            break
        results.append(process_video(filename, preset=preset, start=start, end=end))
    return {"clips": results, "count": len(results),
            "note": "Clips are time-based; no AI highlight selection or virality guarantee."}


def sha256_media(filename: str) -> dict:
    path = _safe_path(filename)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path), "sha256": digest.hexdigest(),
            "note": "For integrity and duplicate management, not to bypass rights enforcement."}
