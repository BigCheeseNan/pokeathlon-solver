from __future__ import annotations

from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from solver_core import (
    SolveOptions,
    list_pokemon_candidates,
    solve_from_pokemon_stars,
    solve_from_star_diffs,
)

intup = tuple[int, ...]


class SolveRequest(BaseModel):
    mode: Literal["diffs", "pokemon"]

    # mode=diffs
    star_diffs: Optional[list[int]] = Field(
        default=None,
        description="5 ints in STAT_FLAVOR order: power, stamina, skill, jump, speed (each in [-4..4])",
    )

    # mode=pokemon
    pokemon_stars: Optional[list[int]] = Field(
        default=None,
        description="5 ints in speed order: speed, power, skill, stamina, jump (each in [1..5])",
    )
    pokemon_top_n: int = 10
    pokemon_data_file: Optional[str] = None

    # shared options
    compute_seed: bool = True
    top_n_solutions: Optional[int] = None
    search_mode: str = "min"  # "min" or "max"
    allowed_x_values: Optional[list[int]] = Field(
        default=None,
        description="Optional list of allowed days (1-31) for seed search. If None, all days allowed."
    )


app = FastAPI(title="Pokeathlon Solver API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


class PokemonCandidatesRequest(BaseModel):
    stars: list[int] = Field(
        description="5 ints in speed order: speed, power, skill, stamina, jump (each in [1..5])"
    )
    pokemon_top_n: int = 10
    pokemon_data_file: Optional[str] = None


@app.post("/api/pokemon/candidates")
def pokemon_candidates(req: PokemonCandidatesRequest) -> object:
    if len(req.stars) != 5:
        raise HTTPException(
            status_code=400, detail="pokemon_stars must be a list of 5 ints"
        )
    stars_list = [int(x) for x in req.stars]
    stars = tuple(stars_list)
    return list_pokemon_candidates(
        stars,
        top_n=req.pokemon_top_n,
        data_file=req.pokemon_data_file,
    )


@app.post("/api/solve")
def solve(req: SolveRequest) -> dict:
    opts = SolveOptions(
        compute_seed=req.compute_seed,
        top_n_solutions=req.top_n_solutions,
        pokemon_top_n=req.pokemon_top_n,
        pokemon_data_file=req.pokemon_data_file,
        search_mode=req.search_mode,
        allowed_x_values=req.allowed_x_values,
    )

    if req.mode == "diffs":
        if req.star_diffs is None or len(req.star_diffs) != 5:
            raise HTTPException(
                status_code=400, detail="star_diffs must be a list of 5 ints"
            )
        diffs_list = [int(x) for x in req.star_diffs]
        diffs = tuple(diffs_list)
        case = solve_from_star_diffs(diffs, options=opts)
        return {"mode": "diffs", "case": case}

    if req.mode == "pokemon":
        if req.pokemon_stars is None or len(req.pokemon_stars) != 5:
            raise HTTPException(
                status_code=400, detail="pokemon_stars must be a list of 5 ints"
            )
        stars_list = [int(x) for x in req.pokemon_stars]
        stars = tuple(stars_list)
        payload = solve_from_pokemon_stars(stars, options=opts)
        return payload

    raise HTTPException(status_code=400, detail="Invalid mode")
