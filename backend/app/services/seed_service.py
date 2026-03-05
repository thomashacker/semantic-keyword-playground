import json
import logging
from pathlib import Path
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.data import DataObject
from weaviate.util import generate_uuid5
from app.models.dataset import DatasetInfo, SeedResponse

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"

DATASET_CONFIGS = {
    "Landmarks": {
        "description": "World-famous landmarks with descriptions, countries, and categories.",
        "fields": ["title", "description", "country", "category"],
        "properties": [
            Property(name="title", data_type=DataType.TEXT),
            Property(name="description", data_type=DataType.TEXT),
            Property(name="country", data_type=DataType.TEXT),
            Property(name="category", data_type=DataType.TEXT),
        ],
        "vectorize_fields": ["title", "description"],
    },
    "Movies": {
        "description": "Classic and contemporary films with plot summaries.",
        "fields": ["title", "plot", "genre", "year"],
        "properties": [
            Property(name="title", data_type=DataType.TEXT),
            Property(name="plot", data_type=DataType.TEXT),
            Property(name="genre", data_type=DataType.TEXT),
            Property(name="year", data_type=DataType.INT),
        ],
        "vectorize_fields": ["title", "plot"],
    },
    "Science": {
        "description": "Scientific concepts with explanations across physics, biology, astronomy, and more.",
        "fields": ["concept", "explanation", "field"],
        "properties": [
            Property(name="concept", data_type=DataType.TEXT),
            Property(name="explanation", data_type=DataType.TEXT),
            Property(name="field", data_type=DataType.TEXT),
        ],
        "vectorize_fields": ["concept", "explanation"],
    },
    "Games": {
        "description": "Steam games with descriptions, genres, and developers.",
        "fields": ["title", "description", "genre", "developer", "year"],
        "properties": [
            Property(name="title", data_type=DataType.TEXT),
            Property(name="description", data_type=DataType.TEXT),
            Property(name="genre", data_type=DataType.TEXT),
            Property(name="developer", data_type=DataType.TEXT),
            Property(name="year", data_type=DataType.INT),
        ],
        "vectorize_fields": ["title", "description"],
    },
    "Pokemon": {
        "description": "Pokémon with Pokédex entries, types, and abilities.",
        "fields": ["title", "description", "type", "generation", "abilities"],
        "properties": [
            Property(name="title", data_type=DataType.TEXT),
            Property(name="description", data_type=DataType.TEXT),
            Property(name="type", data_type=DataType.TEXT),
            Property(name="generation", data_type=DataType.TEXT),
            Property(name="abilities", data_type=DataType.TEXT),
        ],
        "vectorize_fields": ["title", "description"],
    },
}


async def _collection_exists(client: weaviate.WeaviateAsyncClient, name: str) -> bool:
    return await client.collections.exists(name)


async def _get_collection_count(client: weaviate.WeaviateAsyncClient, name: str) -> int:
    try:
        collection = client.collections.get(name)
        result = await collection.aggregate.over_all(total_count=True)
        return result.total_count or 0
    except Exception:
        return 0


async def get_dataset_info(client: weaviate.WeaviateAsyncClient, name: str) -> DatasetInfo:
    config = DATASET_CONFIGS.get(name, {})
    exists = await _collection_exists(client, name)
    count = await _get_collection_count(client, name) if exists else 0
    return DatasetInfo(
        name=name,
        description=config.get("description", ""),
        record_count=count,
        fields=config.get("fields", []),
        seeded=exists and count > 0,
    )


def _title_key(record: dict, config: dict) -> str:
    """Return the title/identifier field value for a record, used for UUID generation."""
    fields = config.get("fields", [])
    # Use first field as the primary key (always the title/concept field)
    key_field = fields[0] if fields else "title"
    return str(record.get(key_field, ""))


async def seed_dataset(client: weaviate.WeaviateAsyncClient, name: str, force: bool = False) -> SeedResponse:
    config = DATASET_CONFIGS[name]
    data_file = DATA_DIR / f"{name.lower()}.json"

    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")

    with open(data_file) as f:
        records = json.load(f)

    exists = await _collection_exists(client, name)

    if exists and force:
        await client.collections.delete(name)
        logger.info(f"Deleted existing collection {name} (force=True)")
        exists = False

    if not exists:
        await client.collections.create(
            name=name,
            properties=config["properties"],
            vector_config=Configure.Vectors.text2vec_openai(model="text-embedding-3-small"),
        )
        logger.info(f"Created collection {name}")

    collection = client.collections.get(name)

    # Build DataObjects with deterministic UUIDs (title-based) to prevent duplicates.
    objects = [
        DataObject(
            properties=record,
            uuid=generate_uuid5(f"{name}:{_title_key(record, config)}"),
        )
        for record in records
        if _title_key(record, config)
    ]

    # Insert in chunks to avoid overwhelming the gRPC connection on large datasets.
    CHUNK_SIZE = 200
    total_inserted = 0
    total_skipped = 0

    for i in range(0, len(objects), CHUNK_SIZE):
        chunk = objects[i : i + CHUNK_SIZE]
        result = await collection.data.insert_many(chunk)
        total_inserted += len(chunk) - len(result.errors)
        total_skipped += len(result.errors)
        logger.info(f"{name}: chunk {i // CHUNK_SIZE + 1}/{(len(objects) - 1) // CHUNK_SIZE + 1} — {total_inserted} inserted so far")

    if total_skipped:
        logger.info(f"{name}: {total_inserted} inserted, {total_skipped} skipped (already exist)")
    else:
        logger.info(f"{name}: {total_inserted} records inserted")

    return SeedResponse(
        dataset=name,
        records_loaded=total_inserted,
        message=f"Seeded {total_inserted} new records into {name}" + (f" ({total_skipped} already existed)" if total_skipped else ""),
    )
