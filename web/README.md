# Pokeathlon Web UI

This repo now includes a local web UI that runs fully in the browser using WASM solvers.

- **Frontend**: React + Vite (TypeScript)
- **WASM**: Emscripten builds of the native C solvers
- **Backend (legacy)**: FastAPI app using the Python solver core

## Layout

- `web/frontend/` Vite React app
- `web/frontend/public/wasm/` WASM solver outputs
- `web/backend/` FastAPI app (legacy backend, optional)

## Build WASM Solvers (Docker)

The WASM solvers are already built and included in the repo, but you can rebuild them after making changes to the C code.
From the repo root:

```bash
docker pull emscripten/emsdk

docker run --rm -v "${PWD}:/src" emscripten/emsdk \
    emcc /src/packages/native/src/recipe/recipe_calculator.c \
    -O3 -s MODULARIZE=1 -s EXPORT_ES6=1 -s ENVIRONMENT=web \
    -s ALLOW_MEMORY_GROWTH=1 \
    -s EXPORTED_FUNCTIONS="['_astar_minimal_recipe_c','_recipe_calc_set_relevant_pruning','_recipe_calc_set_verbose','_malloc','_free']" \
    -s EXPORTED_RUNTIME_METHODS="['ccall']" \
    -o /src/web/frontend/public/wasm/librecipe_calc.js

docker run --rm -v "${PWD}:/src" emscripten/emsdk \
    emcc /src/packages/native/src/seed/hgss_searcher.c \
    /src/packages/native/src/seed/pid_tool.c \
    -O3 -s MODULARIZE=1 -s EXPORT_ES6=1 -s ENVIRONMENT=web \
    -s ALLOW_MEMORY_GROWTH=1 \
    -s EXPORTED_FUNCTIONS="['_pokeathlonFindBestSeedForCriteria','_malloc','_free']" \
    -s EXPORTED_RUNTIME_METHODS="['ccall']" \
    -o /src/web/frontend/public/wasm/libhgss_seedlib.js
```

## Build WASM Solvers (Local Emscripten)

If you have emsdk installed locally, activate it and use `emcc` directly.

```bash
# Example (adjust for your emsdk install location)
emsdk activate latest
source ./emsdk_env.sh

emcc packages/native/src/recipe/recipe_calculator.c \
    -O3 -s MODULARIZE=1 -s EXPORT_ES6=1 -s ENVIRONMENT=web \
    -s ALLOW_MEMORY_GROWTH=1 \
    -s EXPORTED_FUNCTIONS="['_astar_minimal_recipe_c','_recipe_calc_set_relevant_pruning','_recipe_calc_set_verbose','_malloc','_free']" \
    -s EXPORTED_RUNTIME_METHODS="['ccall']" \
    -o web/frontend/public/wasm/librecipe_calc.js

emcc packages/native/src/seed/hgss_searcher.c \
    packages/native/src/seed/pid_tool.c \
    -O3 -s MODULARIZE=1 -s EXPORT_ES6=1 -s ENVIRONMENT=web \
    -s ALLOW_MEMORY_GROWTH=1 \
    -s EXPORTED_FUNCTIONS="['_pokeathlonFindBestSeedForCriteria','_malloc','_free']" \
    -s EXPORTED_RUNTIME_METHODS="['ccall']" \
    -o web/frontend/public/wasm/libhgss_seedlib.js
```

## Frontend (Vite)

From the repo root:

```bash
cd web/frontend
npm install
npm run dev
```

Open:

- http://localhost:5173/

## Backend (FastAPI)

From the repo root:

```bash
py -m pip install -r web/backend/requirements.txt
py -m uvicorn web.backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Notes

- Rebuild the WASM outputs when changing any C files under packages/native/src.
- The solver mode is controlled by web/frontend/.env (VITE_SOLVER_MODE=local).

## Solver Mode (Local vs Remote)

The frontend can run fully in-browser using WASM, or fall back to a remote API.
Set `VITE_SOLVER_MODE` in web/frontend/.env:

- `local`: always use WASM; throw if WASM fails to load or solve.
- `remote`: always use the HTTP API at `/api/*`.
- `auto`: try WASM first and fall back to `/api/*` if local solver fails.
