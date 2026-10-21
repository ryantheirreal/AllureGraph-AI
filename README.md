![SaveFlow brand banner](assets/banner.png)

# SaveFlow — Social Video Studio

**One link in. A social-ready export out.** Download authorized public videos with yt-dlp, then locally create standard MP4s with FFmpeg, minimize descriptive metadata, export short-form ratios, enhance audio, generate covers, and optionally upscale with Real-ESRGAN.

The package is an **open-source local MCP plugin** and **optional self-hosted FastAPI backend**. It is not a hosted video processing service by itself. Installing the private ChatGPT plugin saves its configuration and skills; running its tools from ChatGPT web/mobile requires a separately deployed and connected remote MCP server.

## Features (v0.2.0)

| Capability | Implementation | Limits |
|---|---|---|
| Download best available video/audio | yt-dlp + FFmpeg | Public authorized content, source availability varies |
| Inspect formats/resolutions | yt-dlp | Results depend on extractors |
| Clean descriptive metadata | FFmpeg remux/transcode with `-map_metadata -1` and `-map_chapters -1` | Encoder/container technical metadata may remain; not fingerprint removal |
| Social presets | 9:16 Reels, TikTok, Shorts and Stories, square 1:1, feed 4:5, landscape 16:9, original | Resolution limits prevent runaway rendering |
| Framing | Blurred background, black padding or center crop | Automatic subject tracking is not included |
| Native 2x/4x upscale | Lanczos resampling | Interpolation does **not** restore actual lost detail |
| Optional AI 2x/4x | Real-ESRGAN NCNN Vulkan CLI (if installed) | Suitable GPU and models required; limited duration/frame budget; can alter image details |
| Enhanced audio | EBU-style loudness normalization with FFmpeg `loudnorm` | One-pass normalization, not a mastering service |
| Timed clips / trims | FFmpeg trim, timed batch clips | No automatic highlight ranking |
| Clean cover image | FFmpeg frame JPEG extraction | No automated viral thumbnail design |
| Audio extraction | MP3, M4A, WAV | Must have audio stream |
| SHA-256 integrity check | Python hashlib | Duplicate accounting, not platform fingerprint bypass |
| Export | H.264/AAC MP4 with `+faststart` | Platforms will usually transcode uploads again |

## Supported public platforms

The domain allowlist covers YouTube, TikTok, Instagram, X/Twitter, Reddit, Facebook, Threads, Vimeo, Twitch, Pinterest, SoundCloud, Bluesky, Kick, Rumble, Streamable, Imgur, Tumblr, LinkedIn, Bilibili, Douyin, Snapchat, VK, OK, Bandcamp, Mixcloud, TED, 9GAG, Weibo, Loom and more. **A listed domain does not guarantee every video will work**. Protected/DRM/paywalled/private media are not bypassed.

## Install locally (Python 3.11+, FFmpeg, FFprobe)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[api,test]'
ffmpeg -version && ffprobe -version
python -m server.cli platforms
```

Windows activation: `.venv\\Scripts\\activate`. On Windows, `ffmpeg.exe` and `ffprobe.exe` must be available on PATH. Local MCP clients: connect `mcp.json` (`stdio`, `python -m server.mcp_server`). This MCP process does not directly run inside ChatGPT web/mobile just because the account plugin was saved.

## CLI: download, clean, upscale and export

```bash
# Save a source you have permission to reuse
python -m server.cli download 'https://www.youtube.com/watch?v=YOUR_VIDEO' --quality best

# Paste the actual returned file path for the next commands
python -m server.cli analyze '/path/to/SaveFlow/<job-id>/video.mp4'
python -m server.cli process '/path/to/SaveFlow/<job-id>/video.mp4' --preset reels --framing blur --audio normalize
python -m server.cli process '/path/to/SaveFlow/<job-id>/video.mp4' --preset original --upscale 2x --audio original
python -m server.cli process '/path/to/SaveFlow/<job-id>/video.mp4' --preset shorts --start 10 --end 30 --fps 30
python -m server.cli thumbnail '/path/to/SaveFlow/<job-id>/video.mp4' --at-seconds 2
python -m server.cli audio '/path/to/SaveFlow/<job-id>/video.mp4' --format mp3
python -m server.cli split '/path/to/SaveFlow/<job-id>/video.mp4' --seconds 20 --max-clips 6
```

Sources for local editing must be located under `SAVEFLOW_OUTPUT_DIR` (defaults to `~/Downloads/SaveFlow`) or an explicitly configured `SAVEFLOW_IMPORT_DIR`. Both are sandbox-like path allowlists. Do not point the tool at arbitrary system files.

## MCP tools

- `inspect_video`, `download_video`, `download_and_process`, `supported_platforms`
- `analyze_local_video`, `process_video`, `create_thumbnail`, `extract_audio`
- `split_video_into_clips`, `verify_video_hash`

The tools return actual **local filesystem paths**. They do not silently transmit media to a conversation. The HTTP API can return temporary signed downloads when deployed on a real server.

## Real-ESRGAN optional AI upscale

For actual neural super-resolution, install a release of [Real-ESRGAN NCNN Vulkan](https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan) separately on a compatible machine, including its model folder, and put `realesrgan-ncnn-vulkan` on PATH. Select `upscale="ai2x"` or `"ai4x"`. It decodes a short segment into temporary frames, runs the external binary, then reassembles/re-encodes the result. Default guardrails limit AI to 90 seconds and 600 decoded frames (whichever is shorter); the operation requires substantial storage/GPU resources. Variable-frame-rate timing can be approximate. Non-AI `2x`/`4x` works without that executable but merely interpolates. The AI engine and weights are not redistributed by this project.

## Optional private HTTP API

```bash
pip install -e '.[api]'
export SAVEFLOW_API_TOKEN='set-at-least-24-random-characters'
export SAVEFLOW_PUBLIC_URL='https://YOUR-ACTUAL-DOMAIN'
uvicorn server.api:app --host 0.0.0.0 --port 8000
```

Use HTTPS/TLS termination, persistent secured storage, egress restrictions, rate limits, and authentication. Available endpoints:

- `POST /api/download` — queue a public authorized video URL
- `POST /api/upload` — authorized video upload (200 MiB default limit)
- `POST /api/process` — queue a video already stored on the worker
- `POST /api/download-and-process` — one URL to social-ready export
- `GET /api/jobs/{job_id}` — status and signed file download path (bearer auth)
- `GET /api/files/{job_id}?expires=...&signature=...` — short-lived signed download
- `GET /health` — service health

The API uses a **single-server, in-memory job queue** and ephemeral on-disk media storage. For production multi-worker operation, add durable queues, per-user authentication, observability and automatic deletion policies. A copy of this plugin uploaded to an account **does not deploy this server or configure a cloud MCP endpoint**. The Dockerfile builds the API for a self-hosted container host.

## Environment settings

| Setting | Default | Meaning |
|---|---|---|
| `SAVEFLOW_OUTPUT_DIR` | `~/Downloads/SaveFlow` | Saved media and exports |
| `SAVEFLOW_IMPORT_DIR` | unset | Explicit folder containing imported video files |
| `SAVEFLOW_MAX_BYTES` | 2 GiB | Hard per-file input/output limit |
| `SAVEFLOW_MAX_DURATION` | 3600 sec | Max clip duration to process |
| `SAVEFLOW_TIMEOUT_SECONDS` | 1200 sec | yt-dlp time limit |
| `SAVEFLOW_PROCESS_TIMEOUT` | 1800 sec | FFmpeg processing time limit |
| `SAVEFLOW_MAX_PIXELS` | 14.7M | Pixel safety bound |
| `SAVEFLOW_AI_MAX_SECONDS` | 90 sec | AI segment time bound |
| `SAVEFLOW_AI_MAX_FRAMES` | 600 | AI temporary frame count bound |
| `SAVEFLOW_API_TOKEN` | unset | HTTP bearer secret (required) |
| `SAVEFLOW_UPLOAD_MAX_BYTES` | 200 MiB | Upload limit |
| `SAVEFLOW_PUBLIC_URL` | unset | Actual public HTTPS origin for signed download URLs |

## Testing

```bash
python -m unittest discover -s tests -v
python -m compileall -q server
```

Tests generate synthetic FFmpeg clips. They do not exercise social sites or verify that any user-specific source can be downloaded, nor do they validate installed Real-ESRGAN binaries or cloud-hosted operation.

## Responsible use

Respect platform terms, copyrights and original creators. This project does not remove watermarks, defeat DRM, bypass private access, disguise media fingerprinting, promise that reposted content will be treated as original, or manipulate platform reach. A technically clean MP4 with polished audio and correct dimensions can still be recognized as reused content, and virality depends on creative quality, audience and distribution.

## Open-source dependencies

- [yt-dlp](https://github.com/yt-dlp/yt-dlp), upstream Unlicense — extractors/downloads
- [FFmpeg](https://ffmpeg.org/), LGPL/GPL depending on build — transcoding and metadata processing
- [Real-ESRGAN NCNN Vulkan](https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan) (optional and separately installed) — neural upscaling

SaveFlow's original source: MIT; third-party rights and licenses stay with their authors.


## Instagram Reel inspection and tested URL formats (v0.3.0)

SaveFlow canonicalizes both `/reel/` and `/reels/` links into one canonical URL. For instance,
`https://www.instagram.com/reels/DekknYUiuIX/` becomes
`https://www.instagram.com/reel/DekknYUiuIX/`. This removes only link tracking parameters, not any information stored in the actual video.

```bash
# Default: inspect with yt-dlp; use Apify fallback only if token is configured.
python -m server.cli reel 'https://www.instagram.com/reels/DekknYUiuIX/'
# Explicit Apify metadata scraping of one public Reel (may incur usage charges).
export SAVEFLOW_APIFY_TOKEN='your_apify_token'
python -m server.cli reel 'https://www.instagram.com/reels/DekknYUiuIX/' --provider apify
# Actual video saving uses yt-dlp, and may fail if Instagram blocks anonymous access.
python -m server.cli download 'https://www.instagram.com/reels/DekknYUiuIX/' --quality best
```

For API clients, POST `/api/reel/inspect` with JSON `{ "url": "https://www.instagram.com/reels/DekknYUiuIX/", "provider": "auto" }` and the `SAVEFLOW_API_TOKEN` bearer auth. The Apify integration is optional; no credentials are embedded in this plugin. Scraped `temporary_video_url` is not a locally downloaded MP4.

**Verification status:** Public Instagram data for shortcode `DekknYUiuIX` was retrieved using the Apify connector on 2026-10-20 (1080x1920, 61.17s, creator `eusoumarcoslacerda`). This does not mean the locally packaged plugin ran that connector or produced a downloadable MP4; the hosted server is not connected.

Brand assets: `assets/icon.png` is the 1024px plugin logo, `assets/composer-icon.png` the small composer icon, `assets/banner.png` the repository marketing banner.

## Release 0.4.0: Hosted-ready MCP + Studio

**What is working:** a stateless `POST /mcp` JSON-RPC tool endpoint, six remotely callable tools, a dashboard at `/`, authenticated REST job queue, temporary signed file delivery, FFmpeg presets, and Instagram Reel inspection with optional Apify API token. The tested server is local. **No external cloud instance or domain has been provisioned by the plugin package.**

### Run the web UI and remote MCP server

```bash
pip install -e '.[api]'
export SAVEFLOW_API_TOKEN="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"
export SAVEFLOW_OUTPUT_DIR="$PWD/data"
uvicorn server.api:app --host 127.0.0.1 --port 8000 --workers 1
```

Open `http://127.0.0.1:8000/` and paste your `SAVEFLOW_API_TOKEN` to test the dashboard. Your token only exists in that page's JavaScript memory. If hosting behind HTTPS, set `SAVEFLOW_PUBLIC_URL` to the **actual HTTPS origin** (never a placeholder), so the status tool can return signed download links. The token should be provided by an authenticated remote MCP client as a Bearer secret.

For a production deployment, deploy the Dockerfile on a container/VM with writable persistent `/data`, configure token, HTTPS, egress filtering, rate limits, resource limits, and expose `/mcp`. A sample Render blueprint is provided in `render.yaml` (paid persistent disk needed). **The blueprint itself does not deploy anything.** Keep one application worker because jobs are currently held in memory. Jobs and signed links are lost after a restart; use Redis/object storage before scaling horizontally.

### Remote MCP contract

Send authenticated `POST https://YOUR_DEPLOYED_HOST/mcp` requests with `Content-Type: application/json`, `Authorization: Bearer <your token>`, and JSON-RPC 2.0 bodies. The endpoint implements the stateless JSON response path of MCP Streamable HTTP (`2025-06-18`), with `initialize`, `ping`, `tools/list`, and `tools/call`, and requires a token even for discovery. It does not provide server-sent event streams or server-initiated notifications. Remote tools:

| Tool | Purpose |
|---|---|
| `start_video_download` | Queue a download (one link) |
| `start_video_export` | Queue download + FFmpeg social export |
| `check_video_job` | Poll for completion and a signed file URL |
| `inspect_social_link` | Inspect formats with yt-dlp |
| `inspect_instagram_reel` | Read public Reel data (optionally paid Apify) |
| `list_supported_platforms` | Show allowed social domains |

The remote MCP URL is **not** placed into portable `mcp.json` until a real HTTPS endpoint is confirmed. Existing `mcp.json` continues to configure the local MCP server; installing a private plugin in ChatGPT does **not** start the Python worker or automatically expose remote tools. Connect the remote MCP URL and Bearer credentials through your client's supported connection UI after deployment. Browser origins must be allowlisted via `SAVEFLOW_ALLOWED_ORIGINS`; server-to-server clients that do not send Origin need no origin entry.

Run `python scripts/smoke_test.py --base-url https://YOUR_DEPLOYED_HOST --token-env SAVEFLOW_API_TOKEN` to check a deployed instance without downloading media. This explicitly requires a real, owned endpoint and token.

### Safety and copyright

- Only download and edit media you own, licensed content, or media you have permission to use. Keep attribution when required.
- No login theft, private/paid/DRM bypass, watermark erasure, or claims of viral/fingerprint evasion.
- Social platforms and third-party scrapers can change behavior; no individual URL is guaranteed to work.
- Metadata cleaning removes optional descriptive fields but does not make a file untraceable or reset platform originality signals.
- Do not expose an authenticated yt-dlp worker to untrusted users without network-layer defenses against DNS/redirect SSRF, bandwidth quotas and resource abuse. Link domain checks alone cannot guarantee egress safety.

