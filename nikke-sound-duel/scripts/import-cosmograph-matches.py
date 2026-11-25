#!/usr/bin/env python3
"""Match Apple catalog titles to public uploads from Cosmograph's YouTube channel.

The only media played on the site is the official YouTube IFrame player. This
script reads public YouTube Data API metadata; it does not download video/audio.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "nikke-ost.json"
OUTPUT = ROOT / "data" / "cosmograph-matches.json"
CHANNEL_ID = "UCtup7usUjs_RshOX5LniH-g"
CHANNEL_URL = "https://www.youtube.com/@Cosmograph"
API_ROOT = "https://www.googleapis.com/youtube/v3"
NIKKE_MARKER = re.compile(r"(?:NIKKE|GODDESS\s+OF\s+VICTORY)", re.IGNORECASE)
FRANCHISE_SUFFIX = re.compile(
    r"\s*[\[(][^\])]*(?:NIKKE|GODDESS\s+OF\s+VICTORY)[^\])]*[\])\s*$",
    re.IGNORECASE,
)
VIDEO_SUFFIX = re.compile(
    r"\s*(?:[\(\[]\s*(?:official\s*)?(?:audio|music\s*video|video|m/?v)\s*[\)\]]"
    r"|(?:\s*[-–—|]\s*)?(?:official\s+)?(?:audio|music\s*video|video|m/?v))\s*$",
    re.IGNORECASE,
)


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).casefold()
    return "".join(char for char in text if not unicodedata.combining(char) and char.isalnum())


def request_json(endpoint: str, params: dict, api_key: str) -> dict:
    query = urlencode({**params, "key": api_key})
    request = Request(
        f"{API_ROOT}/{endpoint}?{query}",
        headers={"User-Agent": "NIKKE-Sound-Duel/1.0"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"YouTube Data API returned HTTP {error.code}: {body[:500]}") from None
    except URLError as error:
        raise RuntimeError(f"Could not reach YouTube Data API: {error.reason}") from None


def current_matches() -> dict:
    if OUTPUT.exists():
        try:
            return json.loads(OUTPUT.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "source": "YouTube Data API v3",
        "channelId": CHANNEL_ID,
        "channelUrl": CHANNEL_URL,
        "updatedAt": None,
        "matchedCount": 0,
        "matches": {},
    }


def get_uploads(api_key: str) -> list[dict]:
    channel = request_json("channels", {
        "part": "snippet,contentDetails",
        "id": CHANNEL_ID,
        "maxResults": 1,
    }, api_key)
    items = channel.get("items", [])
    if not items or items[0].get("id") != CHANNEL_ID:
        raise RuntimeError("The configured Cosmograph channel ID was not returned by YouTube.")
    actual_name = items[0].get("snippet", {}).get("title", "")
    if normalize(actual_name) != normalize("Cosmograph"):
        raise RuntimeError(f"Expected the Cosmograph channel, received {actual_name!r}.")
    upload_list = items[0].get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
    if not upload_list:
        raise RuntimeError("YouTube did not return an uploads playlist for Cosmograph.")

    videos: list[dict] = []
    page_token = None
    while True:
        params = {
            "part": "snippet",
            "playlistId": upload_list,
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token
        page = request_json("playlistItems", params, api_key)
        for entry in page.get("items", []):
            snippet = entry.get("snippet", {})
            video_id = snippet.get("resourceId", {}).get("videoId")
            if snippet.get("channelId") != CHANNEL_ID or not video_id:
                continue
            videos.append({
                "id": video_id,
                "title": snippet.get("title", ""),
                "publishedAt": snippet.get("publishedAt", ""),
            })
        page_token = page.get("nextPageToken")
        if not page_token:
            break
    return videos


def title_candidates(video_title: str) -> tuple[list[str], str, bool, bool]:
    has_nikke_marker = bool(NIKKE_MARKER.search(video_title))
    segments = re.split(r"\s*[|｜]\s*", video_title, maxsplit=1)
    body = segments[0].strip() if len(segments) > 1 and has_nikke_marker else video_title.strip()
    body = FRANCHISE_SUFFIX.sub("", body).strip()
    body = VIDEO_SUFFIX.sub("", body).strip()
    if ":" in body or "：" in body:
        separator = ":" if ":" in body else "："
        album_context, song_title = body.rsplit(separator, 1)
        album_context = album_context.strip()
        song_title = VIDEO_SUFFIX.sub("", song_title).strip()
    else:
        album_context = ""
        song_title = body
    candidates = list(dict.fromkeys(value for value in (body, song_title) if normalize(value)))
    is_music_video = bool(re.search(r"\b(?:m/?v|music\s*video)\b", video_title, re.IGNORECASE))
    return candidates, album_context, has_nikke_marker, is_music_video


def match_tracks(tracks: list[dict], videos: list[dict]) -> dict[str, dict]:
    by_title: dict[str, list[dict]] = {}
    for track in tracks:
        key = normalize(track.get("title", ""))
        if key:
            by_title.setdefault(key, []).append(track)

    candidates_by_track: dict[str, list[tuple[tuple[int, int, int, str], dict]]] = {}
    for video in videos:
        title_options, album_context, has_marker, is_music_video = title_candidates(video["title"])
        context_key = normalize(album_context)
        for option in title_options:
            key = normalize(option)
            title_tracks = by_title.get(key, [])
            if not title_tracks:
                continue

            context_matches = [
                track for track in title_tracks
                if context_key and context_key in normalize(track.get("album", ""))
            ]
            if len(title_tracks) > 1:
                if not context_matches:
                    continue
                title_tracks = context_matches

            for track in title_tracks:
                album_match = bool(context_key and context_key in normalize(track.get("album", "")))
                if not has_marker and not album_match:
                    continue
                score = (
                    int(album_match),
                    int(has_marker),
                    int(not is_music_video),
                    video.get("publishedAt", ""),
                )
                value = {
                    "videoId": video["id"],
                    "videoTitle": video["title"],
                    "videoUrl": f"https://www.youtube.com/watch?v={video['id']}",
                }
                candidates_by_track.setdefault(str(track["id"]), []).append((score, value))

    results: dict[str, dict] = {}
    for track_id, candidates in candidates_by_track.items():
        candidates.sort(key=lambda candidate: candidate[0], reverse=True)
        results[track_id] = candidates[0][1]
    return results


def main() -> None:
    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        existing = current_matches()
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(
            json.dumps(existing, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        print(f"YOUTUBE_API_KEY is not set; keeping {existing.get('matchedCount', 0)} existing matches.")
        return

    catalog_data = json.loads(CATALOG.read_text(encoding="utf-8"))
    tracks = catalog_data.get("tracks", [])
    videos = get_uploads(api_key)
    matches = match_tracks(tracks, videos)
    result = {
        "source": "YouTube Data API v3",
        "channelId": CHANNEL_ID,
        "channelUrl": CHANNEL_URL,
        "updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "videoCount": len(videos),
        "matchedCount": len(matches),
        "matches": matches,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Matched {len(matches)} of {len(tracks)} Apple catalog tracks against {len(videos)} Cosmograph uploads.")


if __name__ == "__main__":
    main()

