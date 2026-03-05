"""
Fetches all 1,025 Pokémon from PokeAPI and writes to data/pokemon.json.
Supports resume: safe to cancel and re-run at any time.

Progress is saved after each batch. On restart, already-fetched IDs are skipped.

Usage:
    uv run python -m scripts.fetch_pokemon
"""
import asyncio
import json
import logging
import re
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "pokemon.json"
CHECKPOINT_FILE = DATA_DIR / "pokemon_checkpoint.json"
POKEAPI_BASE = "https://pokeapi.co/api/v2"
BATCH_SIZE = 50
TOTAL = 1025

GENERATION_RANGES = [
    (1, 151, "Generation I"),
    (152, 251, "Generation II"),
    (252, 386, "Generation III"),
    (387, 493, "Generation IV"),
    (494, 649, "Generation V"),
    (650, 721, "Generation VI"),
    (722, 809, "Generation VII"),
    (810, 905, "Generation VIII"),
    (906, 1025, "Generation IX"),
]


def _get_generation(pokemon_id: int) -> str:
    for start, end, gen in GENERATION_RANGES:
        if start <= pokemon_id <= end:
            return gen
    return "Unknown"


def _clean_flavor_text(text: str) -> str:
    return re.sub(r"[\n\f\r]+", " ", text).strip()


def _load_checkpoint() -> set[int]:
    """Return set of already-completed pokemon IDs."""
    if CHECKPOINT_FILE.exists():
        try:
            data = json.loads(CHECKPOINT_FILE.read_text())
            ids = set(data.get("completed_ids", []))
            logger.info(f"Checkpoint: {len(ids)} IDs already fetched")
            return ids
        except Exception:
            pass
    return set()


def _save_checkpoint(completed_ids: set[int]) -> None:
    CHECKPOINT_FILE.write_text(json.dumps({"completed_ids": sorted(completed_ids)}))


def _load_existing_records() -> list[dict]:
    if OUTPUT_FILE.exists():
        try:
            return json.loads(OUTPUT_FILE.read_text())
        except Exception:
            pass
    return []


def _save_records(records: list[dict]) -> None:
    OUTPUT_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False))


async def _fetch_pokemon(client: httpx.AsyncClient, pokemon_id: int) -> dict | None:
    """Fetch pokemon data + species data for a given ID."""
    try:
        pokemon_resp, species_resp = await asyncio.gather(
            client.get(f"{POKEAPI_BASE}/pokemon/{pokemon_id}", timeout=20.0),
            client.get(f"{POKEAPI_BASE}/pokemon-species/{pokemon_id}", timeout=20.0),
        )
        pokemon_resp.raise_for_status()
        species_resp.raise_for_status()
        pokemon = pokemon_resp.json()
        species = species_resp.json()
    except Exception as e:
        logger.warning(f"Failed to fetch pokemon #{pokemon_id}: {e}")
        return None

    name = pokemon.get("name", "").replace("-", " ").title()
    types = [t["type"]["name"].title() for t in pokemon.get("types", [])]
    type_str = "/".join(types) if types else "Unknown"

    abilities = [
        a["ability"]["name"].replace("-", " ").title()
        for a in pokemon.get("abilities", [])
        if not a.get("is_hidden")
    ]
    hidden = [
        a["ability"]["name"].replace("-", " ").title()
        for a in pokemon.get("abilities", [])
        if a.get("is_hidden")
    ]
    abilities_str = ", ".join(abilities)
    if hidden:
        abilities_str += f" (Hidden: {', '.join(hidden)})"

    flavor_entries = [
        _clean_flavor_text(e["flavor_text"])
        for e in species.get("flavor_text_entries", [])
        if e.get("language", {}).get("name") == "en"
    ]
    description = flavor_entries[0] if flavor_entries else f"A {type_str} type Pokémon."

    return {
        "title": name,
        "description": description,
        "type": type_str,
        "generation": _get_generation(pokemon_id),
        "abilities": abilities_str,
    }


async def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    completed_ids = _load_checkpoint()
    records = _load_existing_records()
    logger.info(f"Resuming: {len(records)} records already saved, {TOTAL - len(completed_ids)} IDs remaining")

    remaining_ids = [i for i in range(1, TOTAL + 1) if i not in completed_ids]
    if not remaining_ids:
        logger.info("All Pokémon already fetched!")
        CHECKPOINT_FILE.unlink(missing_ok=True)
        return

    logger.info(f"Fetching {len(remaining_ids)} remaining Pokémon in batches of {BATCH_SIZE}...")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        for batch_start in range(0, len(remaining_ids), BATCH_SIZE):
            batch = remaining_ids[batch_start : batch_start + BATCH_SIZE]
            logger.info(f"  Batch: IDs {batch[0]}–{batch[-1]}")
            results = await asyncio.gather(*[_fetch_pokemon(client, pid) for pid in batch])

            batch_records = []
            for pid, r in zip(batch, results):
                if r is not None:
                    batch_records.append(r)
                completed_ids.add(pid)  # mark done even if None (skip on retry)

            records.extend(batch_records)
            _save_records(records)
            _save_checkpoint(completed_ids)
            logger.info(f"  Saved {len(records)} total records (checkpoint updated)")

            await asyncio.sleep(0.5)

    logger.info(f"Done! {len(records)} Pokémon written to {OUTPUT_FILE}")
    CHECKPOINT_FILE.unlink(missing_ok=True)
    logger.info("Checkpoint file removed.")


if __name__ == "__main__":
    asyncio.run(main())
