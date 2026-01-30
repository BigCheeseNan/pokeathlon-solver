# Pokeathlon Web UI

This repo now includes a local web UI:
- **Frontend**: React + Vite (TypeScript)
- **Backend**: FastAPI (Python)

## Layout

- `web/backend/` FastAPI app
- `web/frontend/` Vite React app
- `recipe_calc/solver_api.py` JSON-friendly solver entrypoints (backend calls this)

## Backend (FastAPI)

From the repo root:

```bash
py -m pip install -r web/backend/requirements.txt
py -m uvicorn web.backend.main:app --reload --port 8000
```

Health check:

- http://localhost:8000/api/health

## Frontend (Vite)

From the repo root:

```bash
cd web/frontend
npm install
npm run dev
```

Open:

- http://localhost:5173/

### Quick Start (PyPI)

With backend and frontend packages already installed:
From the repo root:

```bash
.\start.ps1
```

### Dev proxy

The Vite dev server proxies `/api/*` to `http://localhost:8000` (see `web/frontend/vite.config.ts`).

## API

`POST /api/solve`

Mode `diffs`:

```json
{
  "mode": "diffs",
  "star_diffs": [0, -1, 3, 1, 1],
  "compute_seed": true,
  "top_n_solutions": null
}
```

Mode `pokemon`:

```json
{
  "mode": "pokemon",
  "pokemon_stars": [5, 5, 4, 2, 1],
  "pokemon_top_n": 10,
  "compute_seed": true,
  "top_n_solutions": null
}
```

### Pokemon UI flow

The React UI uses a 2-step flow:

1) `POST /api/pokemon/candidates` to list the top-N candidate Pokemon (fast)
2) When you click a Pokemon, it calls `POST /api/solve` in `diffs` mode using that Pokemon's `computed_diffs`

`POST /api/pokemon/candidates`:

```json
{
  "pokemon_stars": [5, 5, 4, 2, 1],
  "pokemon_top_n": 10
}
```
