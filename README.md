# Pokeathlon Monorepo

This repository contains three main parts:

1) **Solver Core (Python)**
   - Package: packages/solver_core/
   - Provides the core solving logic and a CLI.
   - Pure Python with optional native bindings.

2) **Native Libraries (C/CMake)**
   - Package: packages/native/
   - High-performance C implementations for recipe solving and PID/seed search.
   - Built with CMake; outputs are loaded by the solver core when available.

3) **Web App (Frontend + Backend)**
   - Package: web/
   - FastAPI backend + React/Vite frontend.
   - Uses the solver core for computations.

## Quick Start

- Full stack: run start.ps1 from the repo root.
- Backend: see web/README.md
- Solver core: see packages/solver_core/README.md
- Native libs: see packages/native/README.md
