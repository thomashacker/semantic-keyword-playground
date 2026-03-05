import logging
import random
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List
from app.models.dataset import DatasetInfo, SeedRequest, SeedResponse
from app.services.seed_service import get_dataset_info, seed_dataset
from app.dependencies import get_client
import weaviate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=List[DatasetInfo])
async def list_datasets(client: weaviate.WeaviateAsyncClient = Depends(get_client)):
    datasets = []
    for name in ["Landmarks", "Movies", "Science", "Games", "Pokemon"]:
        info = await get_dataset_info(client, name)
        datasets.append(info)
    return datasets


NATURAL_QUERIES: dict[str, list[str]] = {
    "Landmarks": [
        "where gladiators used to fight",
        "ancient ruins perched on a hill overlooking a city",
        "a tower built for a world's fair that became iconic",
        "massive stone faces carved into a mountainside",
        "a wall built to keep out invaders that stretches for thousands of miles",
        "ruins of a lost city high in the mountains",
        "cathedral that took over a century to build and still isn't finished",
        "a palace built by a king who never got to live in it",
        "ancient wonder in the desert built as a tomb",
        "a rock city carved into rose-red cliffs",
        "temple complex hidden by jungle for centuries",
        "giant waterfall on the border between two countries",
        "statue holding a torch in a harbor welcoming immigrants",
        "ancient circular stone monument aligned with the solstice",
        "a mosque converted into a cathedral then back again",
        "bridge painted international orange spanning a bay",
        "floating city built on a lagoon",
        "white marble mausoleum built by a grieving emperor",
        "terraced citadel of an ancient civilization above the clouds",
        "opera house that looks like sails on the water",
        "temple carved from a single piece of rock",
        "underground salt mine with chapels and sculptures",
        "cliffs at the edge of the world overlooking the Atlantic",
        "ancient theater with perfect acoustics carved into a hillside",
        "geysers and hot springs in a volcanic landscape",
    ],
    "Movies": [
        "film where a man wakes up and realizes the world isn't real",
        "story about a gangster family passing power to the next generation",
        "movie where a character keeps reliving the same day",
        "film where thieves enter people's dreams to steal secrets",
        "a poor family schemes their way into a rich household",
        "animated film about a robot left alone on a ruined Earth",
        "story of survival after being stranded on another planet",
        "film about a man with no memory trying to piece together his past",
        "a child discovers a hidden magical world through a wardrobe",
        "heist where the crew robs the same casino three times",
        "war film told from the perspective of the losing side",
        "two strangers fall in love through letters they shouldn't have read",
        "a musician gives up everything in pursuit of perfection",
        "film about the last survivors of humanity fleeing on a spaceship",
        "detective story where the narrator turns out to be the killer",
        "animated film where emotions are characters living inside a child",
        "story of escape from prison through years of patience",
        "film about a superhero who can shrink to the size of an ant",
        "movie where a woman discovers she is living in a simulated reality",
        "a samurai defends a village against bandits with no pay",
        "story about a jazz musician making a deal with death",
        "film where time runs backwards as memories are recovered",
        "passengers on a luxury ship face disaster at sea",
        "a man with extraordinary memory who can't form new ones",
        "animated coming-of-age story set in a spirit bathhouse",
    ],
    "Science": [
        "why plants turn sunlight into food",
        "invisible force that bends space and pulls objects together",
        "the moment the universe burst into existence",
        "how traits are passed down from parents to children",
        "particles that can be in two places at once",
        "when a star explodes and outshines an entire galaxy",
        "invisible stuff that holds galaxies together but can't be detected",
        "the idea that tiny vibrating strings make up everything",
        "how life changes slowly over millions of generations",
        "cutting and pasting DNA like a word processor",
        "why the sky looks blue but sunsets look orange",
        "how the brain rewires itself when we learn new things",
        "a collapsed star so dense that nothing can escape its pull",
        "the process that copies genetic instructions to build proteins",
        "how vaccines trick the body into building its own defenses",
        "cells that can turn into any type of tissue in the body",
        "the force that keeps planets in orbit around stars",
        "why time moves slower near massive objects",
        "the smallest unit of matter that still behaves like an element",
        "how the immune system remembers past infections",
        "the expansion of the universe accelerating due to unknown energy",
        "how dolphins and bats navigate using sound",
        "what happens inside a star before it dies",
        "the chemical process that makes bread rise and beer ferment",
        "how a single fertilized cell becomes a complete organism",
    ],
    "Games": [
        "open world RPG with magic and sword fighting",
        "space exploration survival game with base building",
        "multiplayer shooter with vehicles and destruction",
        "horror survival game where you hide from monsters",
        "city builder where you manage resources and citizens",
        "puzzle platformer with time manipulation mechanics",
        "turn-based strategy game set in a fantasy world",
        "racing game with car customization and drift mechanics",
        "stealth game where you avoid guards and hack systems",
        "farming simulator with seasons and animal care",
        "roguelike dungeon crawler with procedural generation",
        "cooperative multiplayer game about building and crafting",
        "dark fantasy action RPG with difficult boss fights",
        "narrative adventure game with branching story choices",
        "battle royale game with shrinking map and looting",
    ],
    "Pokemon": [
        "electric mouse pokemon with lightning bolt tail",
        "fire-breathing dragon type that evolves three times",
        "ghost pokemon that haunts old buildings and hospitals",
        "water turtle starter pokemon with cannons on its shell",
        "psychic pokemon that can bend spoons with its mind",
        "legendary dragon pokemon that controls time itself",
        "tiny bug pokemon that transforms into a beautiful butterfly",
        "sleeping pokemon that shares dreams with nearby people",
        "rock type pokemon that looks like a pile of boulders",
        "fairy pokemon that grants wishes to those with pure hearts",
        "ice pokemon that creates blizzards and lives in frozen tundra",
        "grass pokemon with a flower bulb growing on its back",
        "pokemon that mimics other pokemon and transforms perfectly",
        "dark type pokemon that is said to bring misfortune",
        "steel and flying type pokemon inspired by ancient mythology",
    ],
}


@router.get("/{name}/suggestions", response_model=List[str])
async def get_suggestions(
    name: str,
    limit: int = Query(default=5, ge=1, le=20),
):
    valid = {"Landmarks", "Movies", "Science", "Games", "Pokemon"}
    if name not in valid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{name}' not found.")
    pool = NATURAL_QUERIES.get(name, [])
    return random.sample(pool, min(limit, len(pool)))


@router.post("/{name}/seed", response_model=SeedResponse)
async def seed(name: str, request: SeedRequest = SeedRequest(), client: weaviate.WeaviateAsyncClient = Depends(get_client)):
    valid = {"Landmarks", "Movies", "Science", "Games", "Pokemon"}
    if name not in valid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{name}' not found. Valid: {sorted(valid)}",
        )
    try:
        result = await seed_dataset(client, name, force=request.force)
        return result
    except Exception as e:
        logger.error(f"Seed error for {name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Seeding failed: {str(e)}",
        )
