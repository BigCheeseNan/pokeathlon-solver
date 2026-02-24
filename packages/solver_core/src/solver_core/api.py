"""JSON-friendly API for the Pokeathlon recipe/PID solver.

This module is intended to be called from other code (FastAPI backend, notebooks, etc.)
without relying on CLI printing.

It wraps the existing logic and returns JSON-serializable dicts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, TypedDict
from solver_core.constants import (
    STAT_FLAVOR,
    intup,
    SeedSearchResult,
    NATURE_TO_INDEX,
    Result,
)
from solver_core.poke_finder import find_lowest_total_pokemon
from solver_core.main import pokemon_to_star_diffs, find_all_solutions
from solver_core.recipe import astar_minimal_recipe, reduce_recipe


@dataclass(frozen=True)
class SolveOptions:
    compute_seed: bool = True
    top_n_solutions: int | None = None
    pokemon_top_n: int = 10
    pokemon_data_file: str | None = None
    search_mode: str = "min"  # "min" or "max"
    allowed_x_values: list[int] | None = None  # Allowed days (1-31) for seed search


class SeedResultDict(TypedDict, total=False):
    pid: int
    seed: int
    days: list[int]
    streak: int
    count: int
    num_offsets: int
    natural_catch_probability: float


class SolutionDict(TypedDict, total=False):
    ingredients: int
    daily_sum: int
    solver_source: str
    solver_elapsed_s: float | None
    nature: dict[str, Any]
    required_daily: list[int]
    flavors: list[int]
    mildness: int
    recipe_effect: list[int]
    nature_effect: list[int]
    final_mods: list[int]
    grouped_ingredients: list[dict[str, Any]]
    seed_result: SeedResultDict | None


class CaseResultDict(TypedDict, total=False):
    label: str
    desired_star_diffs: list[int]
    solutions_total: int
    solutions_with_recipes: int
    recipe_failures: int
    invalid_seeds: int
    results: list[SolutionDict]
    error: str | None


class PokemonCandidateDict(TypedDict):
    id: int
    dex_id: str
    name: str
    total: int
    base: list[int]
    min: list[int]
    max: list[int]
    computed_diffs: list[int]


class PokemonCandidatesResponseDict(TypedDict):
    mode: str
    desired_stars: list[int]
    candidates: list[PokemonCandidateDict]


def _grouped_to_json(grouped: Iterable[tuple[str, int]]) -> list[dict[str, Any]]:
    return [{"ingredient": ing, "count": cnt} for ing, cnt in grouped]


def _seed_to_json(sr: SeedSearchResult) -> SeedResultDict:
    return {
        "pid": int(sr.pid),
        "seed": int(sr.seed),
        "days": list(sr.x_values),
        "streak": int(sr.streak),
        "count": int(sr.count),
        "num_offsets": int(sr.num_offsets),
        "natural_catch_probability": float(sr.natural_catch_probability),
    }


def _nature_to_json(nat: tuple[str, int, int, bool]) -> dict[str, Any]:
    name, plus_idx, minus_idx, neutral_flag = nat
    return {
        "name": name,
        "plus": STAT_FLAVOR[plus_idx],
        "minus": STAT_FLAVOR[minus_idx],
        "plus_idx": int(plus_idx),
        "minus_idx": int(minus_idx),
        "neutral": bool(neutral_flag),
        "delta": 10 if neutral_flag else 35,
        "index": int(NATURE_TO_INDEX[nat]),
    }


def list_pokemon_candidates(
    desired_stars_speed_order: intup,
    *,
    top_n: int = 10,
    data_file: str | None = None,
) -> PokemonCandidatesResponseDict:
    """List top-N candidate Pokemon for minimum stat requirements.

    Input order: (speed,power,skill,stamina,jump), each in [1..5].

    This is intended for the web UI: show candidates first, and only solve recipes/PIDs
    when the user selects a specific Pokemon.
    """
    for s in desired_stars_speed_order:
        if s < 1 or s > 5:
            raise ValueError("desired_stars_speed_order values must be in [1..5]")

    candidates = find_lowest_total_pokemon(
        desired_stars_speed_order,
        top_n=top_n,
        data_file=data_file,
    )

    return {
        "mode": "pokemon_candidates",
        "desired_stars": list(desired_stars_speed_order),
        "candidates": [
            {
                "id": int(p.id),
                "dex_id": str(p.dex_id),
                "name": p.name,
                "total": int(p.total),
                "base": [
                    int(p.speed),
                    int(p.power),
                    int(p.skill),
                    int(p.stamina),
                    int(p.jump),
                ],
                "min": [
                    int(p.speedMin),
                    int(p.powerMin),
                    int(p.skillMin),
                    int(p.staminaMin),
                    int(p.jumpMin),
                ],
                "max": [
                    int(p.speedMax),
                    int(p.powerMax),
                    int(p.skillMax),
                    int(p.staminaMax),
                    int(p.jumpMax),
                ],
                "computed_diffs": list(
                    pokemon_to_star_diffs(desired_stars_speed_order, p)
                ),
            }
            for p in candidates
        ],
    }


def solve_from_star_diffs(
    desired_star_diffs: intup,
    *,
    options: SolveOptions | None = None,
) -> CaseResultDict:
    """Solve for a single star-diff target.

    desired_star_diffs order is STAT_FLAVOR: (power, stamina, skill, jump, speed), each in [-4..4].

    Returns a dict suitable for JSON.
    """
    opts = options or SolveOptions()

    # Load C solver once (if available) for speed.
    try:
        from solver_core.bindings import c_recipe_wrapper

        c_solver = c_recipe_wrapper.astar_minimal_recipe
    except Exception:
        c_solver = None

    def compute_recipe(flavors: intup) -> tuple[list[str] | None, float | None, str]:
        if c_solver is not None:
            recipe, elapsed, _err = c_solver(flavors, quiet=True, prune_relevant=True)
            return recipe, elapsed, "c"
        recipe = astar_minimal_recipe(flavors)
        return recipe, None, "python"

    solutions = find_all_solutions(desired_star_diffs, mode=opts.search_mode)
    if not solutions:
        return {
            "label": "",
            "desired_star_diffs": list(desired_star_diffs),
            "solutions_total": 0,
            "solutions_with_recipes": 0,
            "recipe_failures": 0,
            "results": [],
            "error": "No feasible (nature, flavor) solution found under the current search space.",
        }

    ranked: list[Result] = []
    skipped_recipes = 0
    invalid_seeds = 0

    for sol in solutions:
        recipe, elapsed, source = compute_recipe(sol.flavors)
        if recipe is None:
            skipped_recipes += 1
            continue

        grouped = reduce_recipe(recipe, sol.flavors)
        seed_result: SeedSearchResult | None = None
        if opts.compute_seed:
            try:
                from solver_core.bindings import find_best_seed_for_criteria

                seed_result = find_best_seed_for_criteria(
                    sol.required_daily,
                    allowed_mod=NATURE_TO_INDEX[sol.nature],
                    allowed_x_values=opts.allowed_x_values,
                    quiet=True,
                )
            except Exception:
                seed_result = None
            if seed_result is None or seed_result.count == 0:
                invalid_seeds += 1
                continue

        final_mods = [
            r + n + d
            for r, n, d in zip(sol.recipe_effect, sol.nature_effect, sol.required_daily)
        ]

        ranked.append(
            Result(
                sol=sol,
                recipe=recipe,
                grouped=grouped,
                elapsed=elapsed,
                source=source,
                ingredients=len(recipe),
                daily_sum=sum(sol.required_daily),
                final_mods=final_mods,
                seed_result=seed_result,
            )
        )

    if not ranked:
        return {
            "label": "",
            "desired_star_diffs": list(desired_star_diffs),
            "solutions_total": len(solutions),
            "solutions_with_recipes": 0,
            "recipe_failures": skipped_recipes,
            "invalid_seeds": invalid_seeds,
            "results": [],
            "error": "Found feasible (nature, flavor) pairs, but no ingredient recipe was produced.",
        }

    if opts.search_mode == "min":
        ranked.sort(
            key=lambda r: (
                r.ingredients,
                r.sol.mildness,
                -r.seed_result.streak if r.seed_result is not None else 10**9,
                -r.seed_result.count if r.seed_result is not None else 10**9,
                NATURE_TO_INDEX[r.sol.nature],
            )
        )
    else:
        ranked.sort(
            key=lambda r: (
                r.seed_result.num_offsets if r.seed_result is not None else -1,
                -r.ingredients,
                -r.sol.mildness,
                r.seed_result.streak if r.seed_result is not None else -1,
                r.seed_result.count if r.seed_result is not None else -1,
                -NATURE_TO_INDEX[r.sol.nature],
            ),
            reverse=True,
        )

    # Return all solutions; frontend will filter for display

    results: list[SolutionDict] = []
    for entry in ranked:
        sol = entry.sol
        results.append(
            {
                "ingredients": int(entry.ingredients),
                "daily_sum": int(entry.daily_sum),
                "solver_source": entry.source,
                "solver_elapsed_s": (
                    float(entry.elapsed) if entry.elapsed is not None else None
                ),
                "nature": _nature_to_json(sol.nature),
                "required_daily": list(sol.required_daily),
                "flavors": list(sol.flavors),
                "mildness": sol.mildness,
                "recipe_effect": list(sol.recipe_effect),
                "nature_effect": list(sol.nature_effect),
                "final_mods": list(entry.final_mods),
                "grouped_ingredients": _grouped_to_json(entry.grouped),
                "seed_result": (
                    _seed_to_json(entry.seed_result)
                    if entry.seed_result is not None
                    else None
                ),
            }
        )

    return {
        "label": "",
        "desired_star_diffs": list(desired_star_diffs),
        "solutions_total": len(solutions),
        "solutions_with_recipes": len(solutions) - skipped_recipes,
        "recipe_failures": skipped_recipes,
        "invalid_seeds": invalid_seeds,
        "results": results,
        "error": None,
    }


def solve_from_pokemon_stars(
    desired_stars_speed_order: intup,
    *,
    options: SolveOptions | None = None,
) -> dict[str, Any]:
    """Pokemon-first mode.

    - Input order: (speed,power,skill,stamina,jump), each in [1..5]
    - Runs find_lowest_total_pokemon(...) to get candidate Pokemon.
    - For each candidate, computes desired_star_diffs = desired - base, with min-stat relaxation,
      then solves using solve_from_star_diffs.

    Returns a JSON-serializable dict with a `cases` list.
    """
    opts = options or SolveOptions()

    for s in desired_stars_speed_order:
        if s < 1 or s > 5:
            raise ValueError("desired_stars_speed_order values must be in [1..5]")

    candidates = find_lowest_total_pokemon(
        desired_stars_speed_order,
        top_n=opts.pokemon_top_n,
        data_file=opts.pokemon_data_file,
    )

    cases: list[CaseResultDict] = []
    for p in candidates:
        diffs = pokemon_to_star_diffs(desired_stars_speed_order, p)
        case = solve_from_star_diffs(diffs, options=opts)
        case["label"] = f"Pokemon={p.name} (id={p.id}) total={p.total}"
        cases.append(case)

    return {
        "mode": "pokemon",
        "desired_stars": list(desired_stars_speed_order),
        "candidates": [
            {
                "id": int(p.id),
                "dex_id": p.dex_id,
                "name": p.name,
                "total": int(p.total),
                "base": [
                    int(p.speed),
                    int(p.power),
                    int(p.skill),
                    int(p.stamina),
                    int(p.jump),
                ],
                "min": [
                    int(p.speedMin),
                    int(p.powerMin),
                    int(p.skillMin),
                    int(p.staminaMin),
                    int(p.jumpMin),
                ],
                "max": [
                    int(p.speedMax),
                    int(p.powerMax),
                    int(p.skillMax),
                    int(p.staminaMax),
                    int(p.jumpMax),
                ],
                "computed_diffs": list(
                    pokemon_to_star_diffs(desired_stars_speed_order, p)
                ),
            }
            for p in candidates
        ],
        "cases": cases,
    }
