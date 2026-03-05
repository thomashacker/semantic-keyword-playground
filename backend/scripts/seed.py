"""
CLI seed script. Usage:
  uv run python -m scripts.seed --dataset all
  uv run python -m scripts.seed --dataset Landmarks
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import weaviate
from app.config import settings
from app.services.seed_service import seed_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

DATASETS = ["Landmarks", "Movies", "Science", "Games", "Pokemon"]


async def main():
    parser = argparse.ArgumentParser(description="Seed Weaviate collections")
    parser.add_argument("--dataset", default="all", help="Dataset name or 'all'")
    parser.add_argument("--force", action="store_true", help="Force re-seed (delete existing)")
    args = parser.parse_args()

    targets = DATASETS if args.dataset == "all" else [args.dataset]

    client = weaviate.use_async_with_weaviate_cloud(
        cluster_url=settings.weaviate_url,
        auth_credentials=weaviate.auth.AuthApiKey(settings.weaviate_api_key),
        headers={"X-OpenAI-Api-Key": settings.openai_api_key},
    )
    await client.connect()

    try:
        for name in targets:
            logger.info(f"Seeding {name}...")
            result = await seed_dataset(client, name, force=args.force)
            logger.info(f"Done: {result.message}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
