import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.lifespan import lifespan
from app.routers import health, search, datasets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

app = FastAPI(
    title="Semantic vs. Keyword Search Playground",
    description="Dual BM25 + semantic search API backed by Weaviate",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(search.router)
app.include_router(datasets.router)
