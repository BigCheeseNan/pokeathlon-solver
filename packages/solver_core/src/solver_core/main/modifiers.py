from solver_core.constants import intup
from .utils import clamp_daily_requirement, weakest_penalty
import math
from typing import Iterable


def star_to_min_modifier(star: int) -> int:
    """Minimum modifier value required to achieve at least this star bonus.

    Star bonuses are in [-4..4].
    """
    if star < -4 or star > 4:
        raise ValueError(f"Star bonus must be in [-4..4], got {star}")

    if star <= -4:
        return -(10**9)  # no lower bound
    if star == -3:
        return -119
    if star == -2:
        return -79
    if star == -1:
        return -39
    if star == 0:
        return -14
    if star == 1:
        return 15
    if star == 2:
        return 40
    if star == 3:
        return 80
    # star == 4 => '>= 120'
    return 120


def apply_nature_effect(nature: tuple[str, int, int, bool]) -> list[int]:
    """Nature contribution in STAT_FLAVOR order.

    Nature rule:
    - neutral nature (flag True): +10 at index1, -10 at index2
    - non-neutral: +35 at index1, -35 at index2

    NOTE: nature indices are assumed to be in STAT_FLAVOR order.
    """
    name, plus_idx, minus_idx, is_neutral = nature
    delta = 10 if is_neutral else 35
    eff = [0, 0, 0, 0, 0]
    eff[plus_idx] += delta
    eff[minus_idx] -= delta
    return eff


def apply_recipe_effect(flavors: intup, mildness: int = 0) -> list[int]:
    """Recipe contribution in STAT_FLAVOR order.

    Recipe rule used by this script:
    - strongest flavor: adds floor(1.5 * x) + 10 to corresponding modifier
    - second strongest: adds floor(1.5 * y)
    - weakest: subtracts (x + y)

    Only those 3 stats are affected.
    """
    # identify indices
    # Tie-breaking rules:
    # - strongest flavor ties: power, stamina, skill, jump, speed
    # - weakest flavor ties: inverted (speed, jump, skill, stamina, power)
    # Our flavor index order is already: (power, stamina, skill, jump, speed).

    if all(f == 0 for f in flavors):
        return [0] * 5

    strongest_idx = max(range(5), key=lambda i: flavors[i])
    weakest_idx = min(range(5), key=lambda i: (flavors[i], -i))

    # second strongest among remaining indices
    remaining = [i for i in range(5) if i != strongest_idx]
    second_idx = max(remaining, key=lambda i: flavors[i])

    x = flavors[strongest_idx]
    y = flavors[second_idx]

    flavor_modifiers = [0] * 5
    flavor_modifiers[strongest_idx] += math.floor(1.5 * x) + 10
    flavor_modifiers[second_idx] += math.floor(1.5 * y)
    flavor_modifiers[weakest_idx] -= weakest_penalty(
        flavors, strongest_idx, second_idx, mildness
    )

    return flavor_modifiers


def required_daily_modifiers(
    desired_stars: intup,
    base_modifiers: Iterable[int],
) -> intup | None:
    """Compute the minimum required daily modifiers (odd ints in [-9..9]) to meet star constraints."""
    mins = [star_to_min_modifier(s) for s in desired_stars]
    reqs: list[int] = []
    for required_min, base in zip(mins, base_modifiers):
        # daily + base >= required_min  => daily >= required_min - base
        need = required_min - base
        req = clamp_daily_requirement(need)
        if req is None:
            return None
        reqs.append(req)
    return tuple(reqs)
