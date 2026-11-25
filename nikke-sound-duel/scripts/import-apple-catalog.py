#!/usr/bin/env python3
"""Refresh Japanese Apple Music catalog metadata; never fetch audio or artwork."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "nikke-ost.json"
STOREFRONT = "jp"
SEARCH_TERMS = (
    "Goddess of Victory NIKKE",
    "NIKKE Original Soundtrack",
    "NIKKE OST",
    "勝利の女神 NIKKE",
)


def get_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "NIKKE-Sound-Duel/1.0"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def search_albums() -> dict[int, dict]:
    albums: dict[int, dict] = {}
    for term in SEARCH_TERMS:
        query = urlencode({
            "term": term,
            "entity": "album",
            "attribute": "albumTerm",
            "limit": 200,
            "country": STOREFRONT,
        })
        result = get_json(f"https://itunes.apple.com/search?{query}")
        for item in result.get("results", []):
            title = item.get("collectionName", "")
            album_id = item.get("collectionId")
            if "NIKKE" in title.upper() and album_id:
                albums[album_id] = item
        time.sleep(0.35)
    return albums


def fetch_tracks(albums: dict[int, dict]) -> list[dict]:
    album_ids = list(albums)
    tracks: dict[int, dict] = {}
    for offset in range(0, len(album_ids), 200):
        batch = album_ids[offset:offset + 200]
        query = urlencode({
            "id": ",".join(map(str, batch)),
            "entity": "song",
            "country": STOREFRONT,
        })
        result = get_json(f"https://itunes.apple.com/lookup?{query}")
        for item in result.get("results", []):
            if item.get("kind") != "song":
                continue
            track_id = item.get("trackId")
            album_id = item.get("collectionId")
            if not track_id or not album_id:
                continue
            track_title = item.get("trackName", "")
            # Apple's JP response contains U+FFFD in this one apostrophe-bearing
            # title. Normalize the known catalog spelling so it can match the
            # same official track title on Cosmograph's channel.
            if track_title.startswith("Standin") and "\ufffd" in track_title:
                track_title = "Standin' by"
            album = albums.get(album_id, {})
            tracks[track_id] = {
                "id": str(track_id),
                "title": track_title,
                "artist": item.get("artistName", ""),
                "album": item.get("collectionName", ""),
                "albumArtist": album.get("artistName", ""),
                "albumId": str(album_id),
                "durationMs": item.get("trackTimeMillis", 0),
                "releaseDate": item.get("releaseDate", "")[:10],
                "appleUrl": item.get("trackViewUrl", ""),
            }
    return sorted(
        tracks.values(),
        key=lambda track: (
            track["album"].casefold(),
            track["title"].casefold(),
            track["id"],
        ),
    )


def main() -> None:
    albums = search_albums()
    tracks = fetch_tracks(albums)
    if not tracks:
        raise SystemExit("Apple's JP catalog returned no NIKKE soundtrack tracks.")
    document = {
        "source": "Apple iTunes Search API",
        "storefront": STOREFRONT,
        "updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "albumCount": len(albums),
        "trackCount": len(tracks),
        "tracks": tracks,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(document, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Imported {len(tracks)} tracks across {len(albums)} Apple Music JP releases.")


if __name__ == "__main__":
    main()

