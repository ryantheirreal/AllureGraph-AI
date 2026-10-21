"""Stateless JSON-over-HTTP MCP endpoint for the SaveFlow authenticated API.

Supports the MCP Streamable HTTP JSON response path for tool clients.
Deploy this module through server.api:app (POST /mcp); no public MCP URL is
claimed until a user-owned server is actually running over HTTPS.
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError

from .downloader import DownloadError

router = APIRouter()
PROTOCOL_VERSION = "2025-06-18"

URL = {"type": "string", "minLength": 10, "maxLength": 2048}
QUALITY = {"type": "string", "enum": ["best", "2160p", "1440p", "1080p", "720p", "480p", "360p"]}
PRESET = {"type": "string", "enum": ["original", "reels", "shorts", "tiktok", "story", "square", "feed", "landscape"]}
UPSCALE = {"type": "string", "enum": ["none", "2x", "4x", "ai2x", "ai4x"]}

def schema(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props, "required": required or [], "additionalProperties": False}

TOOLS = [
    {"name": "start_video_download", "description": "Queue an authorized public social-video download. Returns a job ID; poll check_video_job to retrieve a temporary download link when finished.", "inputSchema": schema({"url": URL, "quality": QUALITY, "audio_only": {"type": "boolean"}}, ["url"])},
    {"name": "start_video_export", "description": "Queue downloading and transcoding to social format with metadata cleanup, audio normalization and optional upscale. Requires user rights to download/reuse the video. A job ID is returned.", "inputSchema": schema({"url": URL, "quality": QUALITY, "preset": PRESET, "upscale": UPSCALE, "framing": {"type": "string", "enum": ["crop", "pad", "blur"]}, "audio": {"type": "string", "enum": ["normalize", "original", "mute"]}}, ["url"])},
    {"name": "check_video_job", "description": "Check status of a queued video job. Returns a temporary signed HTTPS download_url only after completion and if SAVEFLOW_PUBLIC_URL is configured.", "inputSchema": schema({"job_id": {"type": "string", "pattern": "^[a-f0-9]{32}$"}}, ["job_id"])},
    {"name": "inspect_social_link", "description": "Inspect an authorized public social-media link with yt-dlp without downloading the video.", "inputSchema": schema({"url": URL}, ["url"])},
    {"name": "inspect_instagram_reel", "description": "Get public Instagram Reel metadata; provider=auto uses yt-dlp then optional paid Apify fallback when configured.", "inputSchema": schema({"url": URL, "provider": {"type": "string", "enum": ["auto", "yt-dlp", "apify"]}}, ["url"])},
    {"name": "list_supported_platforms", "description": "List recognized social-platform domains, tooling, and available conversion presets.", "inputSchema": schema({})},
]
TOOL_MAP = {tool["name"]: tool for tool in TOOLS}


def _rpc_result(id_: str | int, result: dict) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": id_, "result": result}, headers={"MCP-Protocol-Version": PROTOCOL_VERSION, "Cache-Control": "no-store"})


def _rpc_error(id_: str | int | None, code: int, message: str) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}, headers={"MCP-Protocol-Version": PROTOCOL_VERSION, "Cache-Control": "no-store"})


async def _call_tool(name: str, args: dict, authorization: str) -> dict:
    from .api import DownloadAndProcessRequest, DownloadRequest, create_download, create_download_and_process, get_job
    from .downloader import inspect_video, supported_platforms
    from .instagram import inspect_instagram_reel

    if name not in TOOL_MAP:
        raise ValueError("Unknown tool")
    allowed = TOOL_MAP[name]["inputSchema"]["properties"]
    if set(args) - set(allowed):
        raise ValueError("Unexpected tool argument")
    if name == "start_video_download":
        data = DownloadRequest.model_validate(args)
        return await asyncio.to_thread(create_download, data, authorization)
    if name == "start_video_export":
        data = DownloadAndProcessRequest.model_validate(args)
        return await asyncio.to_thread(create_download_and_process, data, authorization)
    if name == "check_video_job":
        job = args.get("job_id")
        if not isinstance(job, str) or len(job) != 32 or any(c not in "0123456789abcdef" for c in job):
            raise ValueError("Invalid job_id")
        return await asyncio.to_thread(get_job, job, authorization)
    if name == "inspect_social_link":
        return await asyncio.to_thread(inspect_video, args["url"])
    if name == "inspect_instagram_reel":
        return await asyncio.to_thread(inspect_instagram_reel, args["url"], args.get("provider", "auto"))
    if name == "list_supported_platforms":
        return await asyncio.to_thread(supported_platforms)
    raise ValueError("Unknown tool")


@router.post("/mcp")
async def mcp_request(request: Request):
    # Do not accept unauthenticated requests, even for initialize or tools/list.
    from .api import require_auth
    authorization = request.headers.get("authorization")
    require_auth(authorization)
    origin = request.headers.get("origin")
    trusted = {v.strip() for v in os.getenv("SAVEFLOW_ALLOWED_ORIGINS", "").split(",") if v.strip()}
    if origin and origin not in trusted:
        raise HTTPException(status_code=403, detail="Origin is not in SAVEFLOW_ALLOWED_ORIGINS")
    version = request.headers.get("mcp-protocol-version")
    if version and version != PROTOCOL_VERSION:
        raise HTTPException(status_code=400, detail="Unsupported MCP-Protocol-Version")
    accept = request.headers.get("accept", "")
    # MCP clients advertise both supported response formats for POST.
    if "application/json" not in accept or "text/event-stream" not in accept:
        raise HTTPException(status_code=406, detail="Accept must include application/json and text/event-stream")
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
        raise HTTPException(status_code=415, detail="JSON requests only")
    if int(request.headers.get("content-length") or 0) > 64 * 1024:
        raise HTTPException(status_code=413, detail="Request too large")
    raw = await request.body()
    if len(raw) > 64 * 1024:
        raise HTTPException(status_code=413, detail="Request too large")
    try:
        body = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return _rpc_error(None, -32700, "Parse error")
    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0" or not isinstance(body.get("method"), str):
        return _rpc_error(None, -32600, "Invalid JSON-RPC request")
    method = body["method"]
    id_ = body.get("id")
    if "id" not in body:
        if method.startswith("notifications/"):
            return Response(status_code=202)
        return _rpc_error(None, -32600, "Request id required")
    if not isinstance(id_, (str, int)) or isinstance(id_, bool):
        return _rpc_error(None, -32600, "Invalid request id")
    if method == "initialize":
        return _rpc_result(id_, {"protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "SaveFlow Video Studio", "version": "0.4.0"}, "instructions": "Start a video job, then poll check_video_job for a signed download URL. Only process media you have permission to use."})
    if method == "ping":
        return _rpc_result(id_, {})
    if method == "tools/list":
        return _rpc_result(id_, {"tools": TOOLS})
    if method == "tools/call":
        params = body.get("params")
        if not isinstance(params, dict) or not isinstance(params.get("name"), str):
            return _rpc_error(id_, -32602, "Invalid tool call")
        args = params.get("arguments", {})
        if not isinstance(args, dict):
            return _rpc_error(id_, -32602, "Tool arguments must be an object")
        try:
            value = await _call_tool(params["name"], args, authorization or "")
            return _rpc_result(id_, {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, default=str)}], "structuredContent": value, "isError": False})
        except (ValueError, KeyError, DownloadError, ValidationError, HTTPException) as ex:
            message = "Not found" if isinstance(ex, HTTPException) and ex.status_code == 404 else str(getattr(ex, "detail", ex))[:500]
            return _rpc_result(id_, {"content": [{"type": "text", "text": message}], "isError": True})
        except Exception:
            return _rpc_result(id_, {"content": [{"type": "text", "text": "Tool failed; inspect the server logs."}], "isError": True})
    return _rpc_error(id_, -32601, "Method not found")


@router.get("/mcp")
@router.delete("/mcp")
async def unsupported_mcp_transport():
    return Response(status_code=405, headers={"Allow": "POST"})
