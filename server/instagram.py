"""Public Instagram Reel inspection with optional Apify scraping fallback.

Requires SAVEFLOW_APIFY_TOKEN for Apify. Only reads one public Reel; no session
cookies, private profiles or DRM circumvention. Apify may charge per result.
"""
from __future__ import annotations

import json
import os
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from .downloader import DownloadError, inspect_video, validate_url

REEL_PATH = re.compile(r'^/(?:reels|reel)/([A-Za-z0-9_-]{5,32})(?:/|$)')
APIFY_ENDPOINT = 'https://api.apify.com/v2/acts/apify~instagram-scraper/run-sync-get-dataset-items'


def normalize_reel_url(url: str) -> str:
    """Normalize Instagram /reels/ and /reel/ URLs to a stable canonical link."""
    valid = validate_url(url)
    parsed = urlsplit(valid)
    host = (parsed.hostname or '').lower().rstrip('.')
    if host not in {'instagram.com','www.instagram.com','m.instagram.com'}:
        raise DownloadError('Provide an Instagram Reel URL (not another platform).')
    match = REEL_PATH.match(parsed.path)
    if not match:
        raise DownloadError('Expected https://www.instagram.com/reel/SHORTCODE/.')
    return f'https://www.instagram.com/reel/{match.group(1)}/'


def _apify_reel(url: str) -> dict:
    token = os.getenv('SAVEFLOW_APIFY_TOKEN', '')
    if not token:
        raise DownloadError('Set SAVEFLOW_APIFY_TOKEN to enable optional Apify Instagram scraping.')
    payload = json.dumps({'resultsType':'reels','directUrls':[url],'resultsLimit':1}).encode()
    request = Request(APIFY_ENDPOINT, data=payload, method='POST', headers={
        'Authorization':f'Bearer {token}', 'Content-Type':'application/json',
        'Accept':'application/json','User-Agent':'SaveFlow/0.3.0'})
    try:
        with urlopen(request, timeout=110) as response:
            if response.status != 200:
                raise DownloadError(f'Apify returned HTTP {response.status}.')
            limited = response.read(2_000_001)
            if len(limited) > 2_000_000:
                raise DownloadError('Apify response is over size limit.')
        rows=json.loads(limited)
    except (TimeoutError, OSError, ValueError) as ex:
        raise DownloadError('Apify Reel scraper could not complete. Check token and platform access.') from ex
    if not isinstance(rows,list) or not rows:
        raise DownloadError('Apify returned no public Reel data; it may be unavailable.')
    row=rows[0]
    if not isinstance(row,dict) or row.get('shortCode') != urlsplit(url).path.strip('/').split('/')[-1]:
        raise DownloadError('Apify returned a mismatched or invalid Reel result.')
    return {
        'provider':'apify/instagram-scraper',
        'source_url': url,
        'shortcode':row.get('shortCode'),
        'creator':row.get('ownerUsername'),
        'creator_name':row.get('ownerFullName'),
        'caption':row.get('caption'),
        'duration_seconds':row.get('videoDuration'),
        'width':row.get('dimensionsWidth'),
        'height':row.get('dimensionsHeight'),
        'plays':row.get('videoPlayCount'),
        'likes':row.get('likesCount'),
        'comments':row.get('commentsCount'),
        'published_at':row.get('timestamp'),
        'thumbnail_url':row.get('displayUrl'),
        'temporary_video_url':row.get('videoUrl'),
        'note':'Metadata scraped. The temporary CDN URL is not a verified local file. Apify may incur charges; availability varies.',
    }


def inspect_instagram_reel(url: str, provider: str = 'auto') -> dict:
    url=normalize_reel_url(url)
    if provider not in {'auto','yt-dlp','apify'}:
        raise DownloadError('provider must be auto, yt-dlp, or apify.')
    if provider == 'apify':
        return _apify_reel(url)
    try:
        result=inspect_video(url)
        return {'provider':'yt-dlp','shortcode':urlsplit(url).path.strip('/').split('/')[-1],**result}
    except DownloadError:
        if provider == 'yt-dlp' or not os.getenv('SAVEFLOW_APIFY_TOKEN'):
            raise
        return _apify_reel(url)
