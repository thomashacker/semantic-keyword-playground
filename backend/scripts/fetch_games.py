"""
Fetches Steam game data from SteamSpy public API and writes to data/games.json.
Supports resume: safe to cancel and re-run at any time.

SteamSpy pages are always re-fetched (fast, ~40 requests).
Steam store descriptions are cached to data/games_desc_cache.json and reused on resume.

Usage:
    uv run python -m scripts.fetch_games
"""
import asyncio
import json
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "games.json"
DESC_CACHE_FILE = DATA_DIR / "games_desc_cache.json"
TARGET_COUNT = 5000
STEAMSPY_API = "https://steamspy.com/api.php"
STEAM_DETAILS_API = "https://store.steampowered.com/api/appdetails"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tags_to_genre(tags: dict) -> str:
    if not tags:
        return "Unknown"
    top = sorted(tags.items(), key=lambda x: x[1], reverse=True)[:3]
    return ", ".join(name for name, _ in top)


def _craft_description(game: dict) -> str:
    tags = _tags_to_genre(game.get("tags", {}))
    developer = game.get("developer", "Unknown developer")
    publisher = game.get("publisher", "")
    positive = game.get("positive", 0)
    negative = game.get("negative", 0)
    total = positive + negative
    rating = f"{int(positive / total * 100)}% positive" if total > 0 else "unrated"
    parts = [f"A game by {developer}."]
    if tags and tags != "Unknown":
        parts.append(f"Genres: {tags}.")
    if publisher and publisher != developer:
        parts.append(f"Published by {publisher}.")
    parts.append(f"Community rating: {rating} ({total:,} reviews).")
    return " ".join(parts)


def _load_desc_cache() -> dict[int, str]:
    """Load cached appid → description mapping."""
    if DESC_CACHE_FILE.exists():
        try:
            raw = json.loads(DESC_CACHE_FILE.read_text())
            cache = {int(k): v for k, v in raw.items()}
            logger.info(f"Loaded description cache: {len(cache)} entries")
            return cache
        except Exception:
            pass
    return {}


def _save_desc_cache(cache: dict[int, str]) -> None:
    DESC_CACHE_FILE.write_text(json.dumps(cache))


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------

async def _fetch_steamspy_page(client: httpx.AsyncClient, page: int) -> dict:
    for attempt in range(3):
        try:
            resp = await client.get(
                STEAMSPY_API,
                params={"request": "all", "page": page},
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if attempt == 2:
                logger.warning(f"Page {page} failed after 3 attempts: {e}")
                return {}
            await asyncio.sleep(2 ** attempt)
    return {}


async def _fetch_store_description(client: httpx.AsyncClient, appid: int) -> str | None:
    for attempt in range(4):
        try:
            resp = await client.get(
                STEAM_DETAILS_API,
                params={"appids": appid, "filters": "short_description"},
                timeout=15.0,
            )
            if resp.status_code == 429:
                wait = 10 * (attempt + 1)
                logger.warning(f"Steam 429 for appid {appid}, waiting {wait}s")
                await asyncio.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            app_data = data.get(str(appid), {})
            if app_data.get("success") and app_data.get("data"):
                return app_data["data"].get("short_description") or None
            return None
        except Exception:
            pass
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Load description cache (persists across runs)
    desc_cache = _load_desc_cache()

    # --- Step 1: Fetch all SteamSpy pages (fast, always redo) ---
    logger.info("Fetching all SteamSpy pages...")
    all_games: dict[int, dict] = {}

    async with httpx.AsyncClient(follow_redirects=True) as client:
        page = 0
        while True:
            logger.info(f"  Fetching page {page}...")
            page_data = await _fetch_steamspy_page(client, page)
            if not page_data:
                logger.info(f"  Empty page {page}, stopping.")
                break
            all_games.update({int(k): v for k, v in page_data.items()})
            logger.info(f"  Got {len(page_data)} games (total: {len(all_games)})")
            page += 1
            await asyncio.sleep(1.0)
            if len(page_data) < 100:
                break

    logger.info(f"Total raw games: {len(all_games)}")

    # Sort by positive reviews, take top TARGET_COUNT
    sorted_games = sorted(
        all_games.values(),
        key=lambda g: g.get("positive", 0),
        reverse=True,
    )[:TARGET_COUNT]

    # --- Step 2: Fetch store descriptions (cached, resumable) ---
    top_for_description = sorted_games[:200]
    pending = [
        g for g in top_for_description
        if int(g.get("appid", 0)) not in desc_cache and int(g.get("appid", 0)) != 0
    ]
    logger.info(
        f"Store descriptions: {len(desc_cache)} cached, {len(pending)} to fetch"
    )

    async with httpx.AsyncClient(follow_redirects=True) as client:
        for i, game in enumerate(pending):
            appid = int(game.get("appid", 0))
            desc = await _fetch_store_description(client, appid)
            # Cache the result (None means "tried, got nothing" — still cache to skip on resume)
            desc_cache[appid] = desc or ""
            _save_desc_cache(desc_cache)

            if (i + 1) % 25 == 0:
                logger.info(f"  Descriptions fetched: {i + 1}/{len(pending)}")
            # Steam store API: ~200 req/5min → 1 req/1.5s
            await asyncio.sleep(2.0)

    # --- Step 3: Build and write final output ---
    logger.info("Building output records...")
    records = []
    seen_titles: set[str] = set()

    for game in sorted_games:
        title = (game.get("name") or "").strip()
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)

        appid = int(game.get("appid", 0))
        cached_desc = desc_cache.get(appid, "")
        description = cached_desc if cached_desc else _craft_description(game)

        records.append({
            "title": title,
            "description": description,
            "genre": _tags_to_genre(game.get("tags", {})),
            "developer": (game.get("developer") or "Unknown").strip(),
            "year": 0,
        })

    logger.info(f"Writing {len(records)} records to {OUTPUT_FILE}...")
    OUTPUT_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    logger.info(f"Done! {len(records)} games written. Description cache kept at {DESC_CACHE_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
