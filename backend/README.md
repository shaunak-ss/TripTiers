# TripTiers backend (Python / FastAPI)

FastAPI API for three-tier trip generation.

**Start here:** [`../SETUP_GUIDE.md`](../SETUP_GUIDE.md)

```bash
cd backend
cp .env.example .env   # fill keys
uv sync --extra dev    # or: pip install -e ".[dev]"
uv run python -m app.db.seed
uv run uvicorn app.main:app --reload --port 3001
```
