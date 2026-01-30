"""Pokeathlon Solver Core Package.

Public API for solving Pokeathlon stat optimization problems.
"""

from .api import (
    solve_from_star_diffs,
    solve_from_pokemon_stars,
    list_pokemon_candidates,
    SolveOptions,
)

__version__ = "1.0.0"

__all__ = [
    "solve_from_star_diffs",
    "solve_from_pokemon_stars",
    "list_pokemon_candidates",
    "SolveOptions",
]
