# Semantic vs. Keyword Search Playground

An interactive educational split-screen web app that lets you compare **BM25 keyword search** and **semantic vector search** side by side — using real data, powered by [Weaviate](https://weaviate.io/).

Type a query like "landmark in France" and see:
- **Left column (BM25)**: results scored by exact word matches
- **Right column (Semantic)**: results scored by meaning and intent

The key insight: semantic search finds "Eiffel Tower" even though it doesn't contain the words "landmark" or "France".

---

## Datasets

| Dataset | Records | Fields |
|---------|---------|--------|
| Landmarks | 250 | title, description, country, category |
| Movies | 300 | title, plot, genre, year |
| Science | 200 | concept, explanation, field |

---

## Prerequisites

- **Python 3.12+** and [uv](https://docs.astral.sh/uv/)
- **Node 20+** and npm
- **Weaviate Cloud** account ([free tier available](https://console.weaviate.cloud/))
- **OpenAI API key** (for `text-embedding-3-small` vectorization)
- **Docker** (optional, for the Docker Compose workflow)

---

## Quickstart — Option A: Local Development

### 1. Clone and configure

```bash
git clone <repo-url>
cd semantic-keyword-playground
```

**Backend env:**
```bash
cp backend/.env.example backend/.env
# Edit backend/.env and fill in:
# WEAVIATE_URL=https://your-cluster.weaviate.network
# WEAVIATE_API_KEY=your-key
# OPENAI_API_KEY=your-key
```

**Frontend env:**
```bash
cp frontend/.env.local.example frontend/.env.local
# Default: NEXT_PUBLIC_BACKEND_HOST=localhost:8000
```

### 2. Install backend dependencies

```bash
cd backend
uv sync --extra dev
cd ..
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Seed Weaviate collections

```bash
make seed
# Seeds all 3 datasets: Landmarks (250), Movies (300), Science (200)
```

### 5. Start backend

```bash
make dev-backend
# Starts at http://localhost:8000
```

### 6. Start frontend (in a separate terminal)

```bash
make dev-frontend
# Opens http://localhost:3000
```

### 7. Open the playground

Navigate to **http://localhost:3000** and try:
- "landmark in France" → BM25 misses, semantic finds Eiffel Tower
- "film about artificial intelligence and emotions" → semantic finds WALL-E
- "why is the sky blue" → semantic finds Rayleigh Scattering

---

## Quickstart — Option B: Docker Compose

### 1. Configure env

```bash
cp .env.example .env
# Edit .env and fill in your Weaviate and OpenAI credentials
```

### 2. Start

```bash
make docker
# Or: docker compose up --build
```

### 3. Seed data (once running)

```bash
# In a separate terminal:
curl -X POST localhost:8000/datasets/Landmarks/seed
curl -X POST localhost:8000/datasets/Movies/seed
curl -X POST localhost:8000/datasets/Science/seed
```

### 4. Open the playground

Navigate to **http://localhost:3000**

---

## API Reference

### `GET /health`
Returns `{"status": "healthy"}`

### `GET /env_check`
Returns whether required env vars are set.

### `POST /search`
```json
{
  "query": "landmark in France",
  "collection": "Landmarks",
  "limit": 5
}
```
Returns:
```json
{
  "query": "landmark in France",
  "collection": "Landmarks",
  "bm25": [{"title": "...", "description": "...", "score": 1.2, "properties": {}}],
  "semantic": [{"title": "...", "description": "...", "certainty": 0.91, "distance": 0.18, "properties": {}}],
  "timing": {"bm25_ms": 14, "semantic_ms": 52}
}
```

### `GET /datasets`
Returns list of dataset metadata (name, description, record count, fields, seeded status).

### `POST /datasets/{name}/seed`
Seeds a collection. Accepts `{"force": true}` to re-seed.

---

## Running Tests

```bash
make test
# 8 backend tests, all passing
```

---

## Project Structure

```
semantic-keyword-playground/
├── backend/
│   ├── app/            # FastAPI application
│   ├── data/           # Static JSON datasets
│   └── scripts/        # Seed CLI
├── frontend/
│   ├── app/            # Next.js App Router pages
│   ├── components/     # React components
│   └── lib/            # API client
└── tests/
    ├── backend/        # pytest suite (8 tests)
    └── e2e/            # Playwright specs
```

---

## How It Works

1. User types a query
2. Frontend sends `POST /search` to FastAPI
3. Backend runs BM25 and semantic search **concurrently** via `asyncio.gather()`
4. BM25: Weaviate `query.bm25()` — exact word frequency scoring
5. Semantic: Weaviate `query.near_text()` — OpenAI `text-embedding-3-small` embeddings
6. Both results returned with timing data
7. Frontend displays side-by-side with animated cards, score badges, and educational tooltips

---

Built with [Weaviate](https://weaviate.io/) · [FastAPI](https://fastapi.tiangolo.com/) · [Next.js](https://nextjs.org/) · [shadcn/ui](https://ui.shadcn.com/)
