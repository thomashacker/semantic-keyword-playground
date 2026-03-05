.PHONY: dev-backend dev-frontend seed test docker help fetch-games fetch-pokemon expand-data fetch-all

help:
	@echo "Semantic vs. Keyword Search Playground"
	@echo ""
	@echo "Usage:"
	@echo "  make dev-backend    Start FastAPI backend (hot reload)"
	@echo "  make dev-frontend   Start Next.js frontend (hot reload)"
	@echo "  make seed           Seed all Weaviate collections"
	@echo "  make test           Run backend pytest suite"
	@echo "  make docker         Build and start full stack via Docker Compose"
	@echo ""
	@echo "Prerequisites:"
	@echo "  Backend: cp backend/.env.example backend/.env  (fill in credentials)"
	@echo "  Docker:  cp .env.example .env  (fill in credentials)"

dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

dev-frontend:
	cd frontend && npm run dev

seed:
	cd backend && uv run python -m scripts.seed --dataset all

seed-force:
	cd backend && uv run python -m scripts.seed --dataset all --force

test:
	cd backend && uv run pytest ../tests/backend/ -v

docker:
	docker compose up --build

docker-down:
	docker compose down

download-data:
	cd backend && uv run python -m scripts.download_datasets --dataset all

fetch-games:
	cd backend && uv run python -m scripts.fetch_games

fetch-pokemon:
	cd backend && uv run python -m scripts.fetch_pokemon

expand-data:
	cd backend && uv run python -m scripts.expand_datasets

fetch-all: fetch-games fetch-pokemon expand-data
