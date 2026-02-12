# Pokeathlon Monorepo

This repository contains three main parts:

1. **Solver Core (Python)**
    - Package: packages/solver_core/
    - Provides the core solving logic and a CLI.
    - Pure Python with optional native bindings.

2. **Native Libraries (C/CMake)**
    - Package: packages/native/
    - High-performance C implementations for recipe solving and PID/seed search.
    - Built with CMake; outputs are loaded by the solver core when available.

3. **Web App (Frontend + WASM)**
    - Package: web/
    - React/Vite frontend using WASM solvers built from the native C code.
    - Backend is optional/legacy; the UI can run fully in the browser.

## Quick Start

Full frontend:

```bash
npm --prefix web/frontend install

# dev server
npm --prefix web/frontend run dev
# production build 
npm --prefix web/frontend run build
```

With backend:

```bash
py -m pip install -r web/backend/requirements.txt
npm --prefix web/frontend install
.\start.ps1
```

To rebuild WASMs , see the local commands in web/README.md.

- Frontend: see web/README.md
- Solver core (legacy backend): see packages/solver_core/README.md
- Native libs (CMake and WASM builds): see packages/native/README.md
