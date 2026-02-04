"""Link star-bonus requirements to a recipe + PID constraints.

This script connects two problems:
- Given a target flavor vector (5-tuple), compute a minimal ingredient recipe.
- Given a required minimum daily-modifier vector (5-tuple), find PIDs/days-of-month
    that can satisfy those requirements.

This version uses a greedy/heuristic approach for flavors, but now enumerates all
25 natures and ranks every working solution:
1) Try every nature; for each, compute a compact flavor vector that makes the remaining
    requirements feasible.
2) Convert the resulting base modifiers into required daily modifiers (odd ints in [-9..9]).
3) Solve the minimal ingredient recipe for each feasible flavor vector and rank by
    ingredient count (tie-breaker: lower required daily sum, then lexicographic daily).

"""

from solver_core.constants import (
    intup,
    NATURES,
    Solution,
    PAIRS_BY_PRIORITY_PREFER_POWER,
    PAIRS_BY_PRIORITY_PREFER_STAMINA,
)
from .flavors import find_flavors
from .modifiers import (
    apply_nature_effect,
    apply_recipe_effect,
    required_daily_modifiers,
    star_to_min_modifier,
)
from .utils import is_feasible


def _solve_for_nature(
    desired_stars: intup, nat: tuple[str, int, int, bool], mode: str = "min"
) -> Solution | None:
    """Try to build a Solution for a single nature."""
    if mode == "min":
        # Choose the feasible (power, stamina) pair with the highest sum.
        # Tie-break by the stat with the higher desired_star.
        daily_mods = [9] * 5
        prefer_idx = 0 if desired_stars[0] >= desired_stars[1] else 1
        pairs_by_priority = (
            PAIRS_BY_PRIORITY_PREFER_POWER
            if prefer_idx == 0
            else PAIRS_BY_PRIORITY_PREFER_STAMINA
        )

        for _, p, s in pairs_by_priority:
            if is_feasible(nat, p, s):
                daily_mods[0] = p
                daily_mods[1] = s
                break
        else:
            return None
    else:
        daily_mods = [-9] * 5

    modifiers = daily_mods
    modifiers[nat[1]] += 10 if nat[3] else 35
    modifiers[nat[2]] += -10 if nat[3] else -35

    res = find_flavors(desired_stars, modifiers, mode)
    if res is None:
        return None

    flavors, mildness = res

    assert sum(flavors) <= 100, f"Flavor sum exceeds 100: {flavors}"
    assert all(f <= 63 for f in flavors), f"Flavor exceeds per-flavor cap 63: {flavors}, mode={mode}"

    modifiers = apply_recipe_effect(flavors, mildness)
    modifiers[nat[1]] += 10 if nat[3] else 35
    modifiers[nat[2]] += -10 if nat[3] else -35

    min_daily_mods = required_daily_modifiers(desired_stars, modifiers)
    if min_daily_mods is None:
        return None

    if any(
        d + m < star_to_min_modifier(s)
        for d, m, s in zip(min_daily_mods, modifiers, desired_stars)
    ):
        return None

    return Solution(
        nature=nat,
        flavors=flavors,
        recipe_effect=tuple(apply_recipe_effect(flavors, mildness)),
        nature_effect=tuple(apply_nature_effect(nat)),
        required_daily=min_daily_mods,
        mildness=mildness,
    )


def find_all_solutions(desired_stars: intup, mode: str = "min") -> list[Solution]:
    """Enumerate all nature choices (25) and collect feasible solutions.

    Input order: STAT_FLAVOR (power, stamina, skill, jump, speed).
    """
    positive_stars = [(i, s) for i, s in enumerate(desired_stars) if s > 0]
    negative_stars = [(i, s) for i, s in enumerate(desired_stars) if s < 0]
    if len(positive_stars) > 3:
        return []
    elif max(desired_stars) > 3 and len(positive_stars) > 2:
        return []
    elif desired_stars.count(4) > 1:
        return []
    elif sum(s for i, s in positive_stars) > 8:
        return []
    elif desired_stars.count(4) == 1 and len(negative_stars) == 0:
        return []

    forced_4_idx = desired_stars.index(4) if desired_stars.count(4) == 1 else None

    results: list[Solution] = []
    for nat in NATURES:
        if forced_4_idx is not None and (nat[3] or nat[1] != forced_4_idx):
            continue
        sol = _solve_for_nature(desired_stars, nat, mode)
        if sol is not None:
            results.append(sol)
    return results
