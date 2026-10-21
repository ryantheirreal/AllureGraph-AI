"""Local CLI to use SaveFlow Video Studio without an MCP host."""
import argparse
import json
from .downloader import inspect_video, download_video, supported_platforms, DownloadError
from .instagram import inspect_instagram_reel
from .processor import process_video, media_info, create_thumbnail, extract_audio, split_clips

def main():
    p = argparse.ArgumentParser(description="SaveFlow social video studio")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("platforms")
    for cmd in ("inspect", "reel", "analyze", "thumbnail", "audio", "split", "process", "download"):
        parser = sub.add_parser(cmd)
        parser.add_argument("url" if cmd in ("inspect", "reel", "download") else "path")
        if cmd == "reel":
            parser.add_argument("--provider", choices=["auto","yt-dlp","apify"], default="auto")
        if cmd == "download":
            parser.add_argument("--quality", default="best")
            parser.add_argument("--audio-only", action="store_true")
        elif cmd == "process":
            parser.add_argument("--preset", default="reels")
            parser.add_argument("--upscale", default="none")
            parser.add_argument("--framing", default="blur")
            parser.add_argument("--fps", default="source")
            parser.add_argument("--audio", default="normalize")
            parser.add_argument("--start", type=float, default=0)
            parser.add_argument("--end", type=float)
            parser.add_argument("--crf", type=int, default=19)
        elif cmd == "thumbnail":
            parser.add_argument("--at-seconds", type=float, default=1)
        elif cmd == "audio":
            parser.add_argument("--format", default="mp3")
        elif cmd == "split":
            parser.add_argument("--seconds", type=int, default=30)
            parser.add_argument("--max-clips", type=int, default=8)
            parser.add_argument("--preset", default="reels")
    args = p.parse_args()
    try:
        if args.cmd == "platforms": out = supported_platforms()
        elif args.cmd == "inspect": out = inspect_video(args.url)
        elif args.cmd == "reel": out = inspect_instagram_reel(args.url, args.provider)
        elif args.cmd == "download": out = download_video(args.url, args.quality, args.audio_only)
        elif args.cmd == "analyze": out = media_info(args.path)
        elif args.cmd == "thumbnail": out = create_thumbnail(args.path, args.at_seconds)
        elif args.cmd == "audio": out = extract_audio(args.path, args.format)
        elif args.cmd == "split": out = split_clips(args.path, args.seconds, args.max_clips, args.preset)
        else: out = process_video(args.path, args.preset, args.upscale, args.framing, args.fps,
                                  args.audio, args.start, args.end, args.crf)
        print(json.dumps(out, indent=2, ensure_ascii=False))
    except (DownloadError, ValueError, FileNotFoundError) as ex:
        p.exit(1, f"SaveFlow error: {ex}\n")

if __name__ == "__main__":
    main()
