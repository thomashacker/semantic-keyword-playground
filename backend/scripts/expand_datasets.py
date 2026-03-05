"""
Expands existing Landmarks, Movies, and Science datasets using Wikipedia's free API.
Merges with existing JSON files, deduplicates by title, and writes back.
Supports resume: progress is flushed to disk every 25 records. Safe to cancel and re-run.

Usage:
    uv run python -m scripts.expand_datasets
"""
import asyncio
import json
import logging
import re
import urllib.parse
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

DATA_DIR = Path(__file__).parent.parent / "data"
WP_API = "https://en.wikipedia.org/w/api.php"
WP_REST = "https://en.wikipedia.org/api/rest_v1/page/summary"

# Wikipedia requires a descriptive User-Agent with contact info
USER_AGENT = "SemanticKeywordPlayground/1.0 (https://github.com/weaviate/semantic-keyword-playground; bot)"

# Time to wait between API requests (seconds) — be polite to Wikipedia
REQUEST_DELAY = 1.0
# Max retries on 429/503
MAX_RETRIES = 4


# ---------------------------------------------------------------------------
# Wikipedia helpers
# ---------------------------------------------------------------------------

async def _get_with_retry(client: httpx.AsyncClient, url: str, params: dict) -> httpx.Response | None:
    """GET with exponential backoff on 429/503/403."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = await client.get(url, params=params, timeout=20.0)
            if resp.status_code in (429, 503):
                wait = 2 ** (attempt + 1)
                logger.warning(f"Rate limited ({resp.status_code}), waiting {wait}s (attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(wait)
                continue
            if resp.status_code == 403:
                wait = 3 ** (attempt + 1)
                logger.warning(f"403 Forbidden, waiting {wait}s (attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except httpx.TimeoutException:
            wait = 2 ** attempt
            logger.warning(f"Timeout, retrying in {wait}s")
            await asyncio.sleep(wait)
        except httpx.HTTPStatusError:
            raise
    return None


async def _category_members(client: httpx.AsyncClient, category: str, limit: int = 500) -> list[str]:
    """Return page titles in a Wikipedia category, sequentially."""
    titles = []
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category}",
        "cmlimit": min(limit, 500),
        "cmtype": "page",
        "format": "json",
    }
    cmcontinue = None
    while len(titles) < limit:
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        try:
            resp = await _get_with_retry(client, WP_API, params)
            if resp is None:
                logger.warning(f"Category '{category}' gave up after retries")
                break
            data = resp.json()
            members = data.get("query", {}).get("categorymembers", [])
            titles.extend(m["title"] for m in members)
            cmcontinue = data.get("continue", {}).get("cmcontinue")
            if not cmcontinue:
                break
            await asyncio.sleep(REQUEST_DELAY)
        except Exception as e:
            logger.warning(f"Category '{category}' error: {e}")
            break
    return titles[:limit]


async def _page_summary(client: httpx.AsyncClient, title: str) -> dict | None:
    """Fetch Wikipedia REST summary for a page title, with retry."""
    encoded = urllib.parse.quote(title.replace(" ", "_"), safe="")
    url = f"{WP_REST}/{encoded}"
    for attempt in range(MAX_RETRIES):
        try:
            resp = await client.get(url, timeout=15.0)
            if resp.status_code == 404:
                return None
            if resp.status_code in (429, 503):
                wait = 2 ** (attempt + 1)
                await asyncio.sleep(wait)
                continue
            if resp.status_code == 403:
                wait = 3 ** (attempt + 1)
                await asyncio.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except httpx.TimeoutException:
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logger.debug(f"Summary error for '{title}': {e}")
            break
    return None


# ---------------------------------------------------------------------------
# Landmarks expansion
# ---------------------------------------------------------------------------

LANDMARK_CATEGORIES = [
    "World_Heritage_Sites_by_country",
    "Wonders_of_the_world",
    "Ancient_landmarks",
    "Castles_by_country",
    "Cathedrals_by_country",
    "Bridges_by_country",
    "Famous_mountains",
    "National_monuments_of_the_United_States",
    "Landmarks_in_Europe",
    "Landmarks_in_Asia",
    "Landmarks_in_Africa",
    "National_parks_by_country",
]

COUNTRY_HINTS = {
    "United States": ["united states", "american", "u.s.", "usa"],
    "France": ["france", "french", "paris"],
    "Italy": ["italy", "italian", "rome"],
    "China": ["china", "chinese", "beijing"],
    "India": ["india", "indian", "delhi"],
    "United Kingdom": ["united kingdom", "british", "england", "london"],
    "Japan": ["japan", "japanese", "tokyo"],
    "Egypt": ["egypt", "egyptian", "cairo"],
    "Mexico": ["mexico", "mexican"],
    "Peru": ["peru", "peruvian"],
    "Greece": ["greece", "greek", "athens"],
    "Spain": ["spain", "spanish", "madrid"],
    "Germany": ["germany", "german", "berlin"],
}

LANDMARK_CATEGORY_MAP = {
    "castle": "Castle", "cathedral": "Cathedral", "bridge": "Bridge",
    "mountain": "Natural", "park": "Natural", "temple": "Temple",
    "mosque": "Religious", "church": "Religious", "palace": "Palace",
    "monument": "Monument", "museum": "Museum", "ruins": "Ruins",
    "fort": "Fort", "lighthouse": "Lighthouse", "tower": "Tower",
}


def _guess_country(title: str, summary_text: str) -> str:
    text = f"{title} {summary_text}".lower()
    for country, hints in COUNTRY_HINTS.items():
        if any(h in text for h in hints):
            return country
    return "Unknown"


def _guess_landmark_category(title: str, summary_text: str) -> str:
    text = f"{title} {summary_text}".lower()
    for keyword, cat in LANDMARK_CATEGORY_MAP.items():
        if keyword in text:
            return cat
    return "Landmark"


FLUSH_EVERY = 25


def _flush(path: Path, all_records: list[dict]) -> None:
    path.write_text(json.dumps(all_records, indent=2, ensure_ascii=False))


async def expand_landmarks(
    client: httpx.AsyncClient,
    existing_records: list[dict],
    existing_titles: set[str],
    output_path: Path,
    target: int = 1250,
) -> list[dict]:
    logger.info("Expanding Landmarks dataset...")
    all_titles: list[str] = []

    for cat in LANDMARK_CATEGORIES:
        logger.info(f"  Fetching category: {cat}")
        titles = await _category_members(client, cat, limit=200)
        new = [t for t in titles if t not in existing_titles]
        all_titles.extend(new)
        logger.info(f"    Got {len(titles)} titles, {len(new)} new")
        await asyncio.sleep(REQUEST_DELAY)

    unique = list(dict.fromkeys(all_titles))
    logger.info(f"  Found {len(unique)} candidate landmark pages")

    new_records: list[dict] = []
    since_flush = 0
    for title in unique:
        if len(new_records) >= target:
            break
        if title in existing_titles:
            continue
        await asyncio.sleep(REQUEST_DELAY)
        s = await _page_summary(client, title)
        if s is None:
            continue
        extract = s.get("extract", "").strip()
        if not extract or len(extract) < 50 or "may refer to" in extract.lower():
            continue
        existing_titles.add(title)
        new_records.append({
            "title": title,
            "description": extract[:500],
            "country": _guess_country(title, extract),
            "category": _guess_landmark_category(title, extract),
        })
        since_flush += 1
        if since_flush >= FLUSH_EVERY:
            _flush(output_path, existing_records + new_records)
            since_flush = 0
            logger.info(f"    Flushed. Landmarks collected: {len(new_records)}/{target}")

    _flush(output_path, existing_records + new_records)
    logger.info(f"  Expanded landmarks by {len(new_records)} records")
    return new_records


# ---------------------------------------------------------------------------
# Movies expansion
# ---------------------------------------------------------------------------

MOVIE_CATEGORIES = [
    "American_films_of_the_1970s",
    "American_films_of_the_1980s",
    "American_films_of_the_1990s",
    "American_films_of_the_2000s",
    "American_films_of_the_2010s",
    "American_films_of_the_2020s",
    "British_films_of_the_1990s",
    "British_films_of_the_2000s",
    "French_films_of_the_2000s",
    "Academy_Award_for_Best_Picture_winners",
    "Science_fiction_films",
    "Horror_films",
    "Animated_films",
]

DECADE_MAP = {
    "1970": 1975, "1980": 1985, "1990": 1995,
    "2000": 2005, "2010": 2015, "2020": 2022,
}

GENRE_HINTS = {
    "Horror": ["horror", "terror", "slasher", "haunted", "zombie"],
    "Comedy": ["comedy", "comedic", "funny", "humor", "sitcom"],
    "Action": ["action", "thriller", "adventure", "spy", "heist"],
    "Drama": ["drama", "dramatic", "emotional"],
    "Sci-Fi": ["science fiction", "sci-fi", "space", "robot", "alien", "futuristic"],
    "Animation": ["animated", "animation", "cartoon", "pixar", "disney"],
    "Romance": ["romance", "romantic", "love story"],
    "Documentary": ["documentary", "real", "based on a true"],
}


def _guess_genre(title: str, extract: str) -> str:
    text = f"{title} {extract}".lower()
    for genre, hints in GENRE_HINTS.items():
        if any(h in text for h in hints):
            return genre
    return "Drama"


def _guess_year(category: str, extract: str) -> int:
    for decade_str, year in DECADE_MAP.items():
        if decade_str in category:
            return year
    m = re.search(r"\b(19[5-9]\d|20[0-2]\d)\b", extract)
    if m:
        return int(m.group(1))
    return 2000


async def expand_movies(
    client: httpx.AsyncClient,
    existing_records: list[dict],
    existing_titles: set[str],
    output_path: Path,
    target: int = 1700,
) -> list[dict]:
    logger.info("Expanding Movies dataset...")
    all_titles: list[str] = []
    title_to_cat: dict[str, str] = {}

    for cat in MOVIE_CATEGORIES:
        logger.info(f"  Fetching category: {cat}")
        titles = await _category_members(client, cat, limit=200)
        for t in titles:
            if t not in existing_titles and t not in title_to_cat:
                title_to_cat[t] = cat
                all_titles.append(t)
        logger.info(f"    Got {len(titles)} titles")
        await asyncio.sleep(REQUEST_DELAY)

    unique = list(dict.fromkeys(all_titles))
    logger.info(f"  Found {len(unique)} candidate movie pages")

    new_records: list[dict] = []
    since_flush = 0
    for title in unique:
        if len(new_records) >= target:
            break
        if title in existing_titles:
            continue
        await asyncio.sleep(REQUEST_DELAY)
        s = await _page_summary(client, title)
        if s is None:
            continue
        extract = s.get("extract", "").strip()
        if not extract or len(extract) < 50 or "may refer to" in extract.lower():
            continue
        existing_titles.add(title)
        cat = title_to_cat.get(title, "")
        new_records.append({
            "title": title,
            "plot": extract[:600],
            "genre": _guess_genre(title, extract),
            "year": _guess_year(cat, extract),
        })
        since_flush += 1
        if since_flush >= FLUSH_EVERY:
            _flush(output_path, existing_records + new_records)
            since_flush = 0
            logger.info(f"    Flushed. Movies collected: {len(new_records)}/{target}")

    _flush(output_path, existing_records + new_records)
    logger.info(f"  Expanded movies by {len(new_records)} records")
    return new_records


# ---------------------------------------------------------------------------
# Science expansion
# ---------------------------------------------------------------------------

SCIENCE_CATEGORIES = [
    "Physics_concepts",
    "Biology_concepts",
    "Astronomy",
    "Chemistry_concepts",
    "Quantum_mechanics",
    "Thermodynamics",
    "Evolutionary_biology",
    "Molecular_biology",
    "Neuroscience",
    "Genetics",
    "Mathematics_concepts",
    "Computer_science",
    "Ecology",
]

FIELD_HINTS = {
    "Physics": ["physics", "quantum", "force", "energy", "particle", "thermodynamics", "electro"],
    "Biology": ["biology", "cell", "gene", "organism", "evolution", "ecology", "species"],
    "Chemistry": ["chemistry", "molecule", "chemical", "reaction", "compound", "element"],
    "Astronomy": ["astronomy", "star", "galaxy", "planet", "cosmos", "universe", "space"],
    "Mathematics": ["mathematics", "theorem", "equation", "calculus", "algebra", "geometry"],
    "Computer Science": ["computing", "algorithm", "program", "software", "data", "network"],
    "Neuroscience": ["brain", "neuron", "cognition", "neural", "synapse"],
    "Genetics": ["dna", "rna", "genome", "chromosome", "heredity", "gene"],
}


def _guess_field(title: str, extract: str) -> str:
    text = f"{title} {extract}".lower()
    for field, hints in FIELD_HINTS.items():
        if any(h in text for h in hints):
            return field
    return "Science"


async def expand_science(
    client: httpx.AsyncClient,
    existing_records: list[dict],
    existing_titles: set[str],
    output_path: Path,
    target: int = 800,
) -> list[dict]:
    logger.info("Expanding Science dataset...")
    all_titles: list[str] = []

    for cat in SCIENCE_CATEGORIES:
        logger.info(f"  Fetching category: {cat}")
        titles = await _category_members(client, cat, limit=150)
        new = [t for t in titles if t not in existing_titles]
        all_titles.extend(new)
        logger.info(f"    Got {len(titles)} titles, {len(new)} new")
        await asyncio.sleep(REQUEST_DELAY)

    unique = list(dict.fromkeys(all_titles))
    logger.info(f"  Found {len(unique)} candidate science pages")

    new_records: list[dict] = []
    since_flush = 0
    for title in unique:
        if len(new_records) >= target:
            break
        if title in existing_titles:
            continue
        await asyncio.sleep(REQUEST_DELAY)
        s = await _page_summary(client, title)
        if s is None:
            continue
        extract = s.get("extract", "").strip()
        if not extract or len(extract) < 50 or "may refer to" in extract.lower():
            continue
        existing_titles.add(title)
        new_records.append({
            "concept": title,
            "explanation": extract[:500],
            "field": _guess_field(title, extract),
        })
        since_flush += 1
        if since_flush >= FLUSH_EVERY:
            _flush(output_path, existing_records + new_records)
            since_flush = 0
            logger.info(f"    Flushed. Science collected: {len(new_records)}/{target}")

    _flush(output_path, existing_records + new_records)
    logger.info(f"  Expanded science by {len(new_records)} records")
    return new_records


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        # --- Landmarks ---
        landmarks_file = DATA_DIR / "landmarks.json"
        existing_landmarks: list[dict] = []
        if landmarks_file.exists():
            existing_landmarks = json.loads(landmarks_file.read_text())
        existing_landmark_titles = {r["title"] for r in existing_landmarks}
        logger.info(f"Landmarks: {len(existing_landmarks)} existing records")
        await expand_landmarks(client, existing_landmarks, existing_landmark_titles, landmarks_file, target=1250)
        logger.info(f"Landmarks: done ({landmarks_file})")

        # --- Movies ---
        movies_file = DATA_DIR / "movies.json"
        existing_movies: list[dict] = []
        if movies_file.exists():
            existing_movies = json.loads(movies_file.read_text())
        existing_movie_titles = {r["title"] for r in existing_movies}
        logger.info(f"Movies: {len(existing_movies)} existing records")
        await expand_movies(client, existing_movies, existing_movie_titles, movies_file, target=1700)
        logger.info(f"Movies: done ({movies_file})")

        # --- Science ---
        science_file = DATA_DIR / "science.json"
        existing_science: list[dict] = []
        if science_file.exists():
            existing_science = json.loads(science_file.read_text())
        existing_science_titles = {r["concept"] for r in existing_science}
        logger.info(f"Science: {len(existing_science)} existing records")
        await expand_science(client, existing_science, existing_science_titles, science_file, target=800)
        logger.info(f"Science: done ({science_file})")

    logger.info("All datasets expanded successfully!")


if __name__ == "__main__":
    asyncio.run(main())
