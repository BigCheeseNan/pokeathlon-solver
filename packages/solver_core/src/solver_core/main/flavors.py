from solver_core.constants import intup
from .modifiers import star_to_min_modifier
from .utils import weakest_penalty
import math


def min_required_mildness(
    diffs: list[int], max_flav: int, second_flav: int, decrease_idx: int
) -> int:
    min_diff = diffs[decrease_idx]
    decrease = max_flav + second_flav
    if decrease <= -min_diff:
        return 0
    for mildness in range(0, 200, 25):
        adjusted_decrease = (decrease * (100 - (mildness // 25) * 10)) // 100
        if adjusted_decrease <= -min_diff:
            return mildness
    if decrease * 20 // 100 <= -min_diff:
        return 200
    else:
        return 255


def find_flavors(
    desired_stars: intup,
    modifiers: list[int],
    mode: str = "min",
) -> tuple[intup, int] | None:
    """Core flavor-finding logic for both min and max modes.

    Args:
        desired_stars: Target star bonuses in STAT_FLAVOR order (power, stamina, skill, jump, speed)
        modifiers: Base modifiers after nature effects
        mode: "min" for minimal ingredients (mildness=0), "max" for better seeds (mildness=255)

    Returns:
        5-tuple of flavor values, or None if constraints cannot be satisfied (min mode only)

    Strategy:
        - Identify the two largest stat gaps (strongest and second-strongest flavors)
        - Assign base flavor values to cover these gaps
        - Fill remaining flavors to satisfy weakest-penalty constraints
        - Add +1 and +2 deltas to prefer even values and multiples of 4
    """
    diffs = [star_to_min_modifier(s) - m for s, m in zip(desired_stars, modifiers)]
    flavors = [0] * 5

    if all(d <= 0 for d in diffs):
        return tuple(flavors), 0

    second_idx, max_idx = sorted(range(5), key=lambda i: (diffs[i], -i))[-2:]
    max_diff, second_diff = diffs[max_idx], diffs[second_idx]

    if mode == "min":
        second_flav = max(0, math.ceil(second_diff / 1.5))
        max_flav = max(math.ceil((max_diff - 10) / 1.5), second_flav)
    else:
        second_flav = min(max(0, math.ceil(second_diff / 1.5)), 50)
        max_flav = min(
            max(math.ceil((max_diff - 10) / 1.5), second_flav),
            min(100 - second_flav, 63),
        )

    if mode == "min" and (max_flav > 63 or max_flav + second_flav > 100):
        return None
    if max_idx > second_idx and max_flav == second_flav:
        max_flav += 1
        if max_flav + second_flav > 100:
            second_flav -= 1

    flavors[second_idx], flavors[max_idx] = second_flav, max_flav

    decrease = second_flav + max_flav
    decrease_idx: int | None = None

    decrease_idx = next(
        (i for i in range(4, -1, -1) if decrease <= -diffs[i]),
        min(range(5), key=lambda i: (diffs[i], -i)),
    )

    for i in range(4, decrease_idx, -1):
        if flavors[i] == 0:
            flavors[i] += 1

    # Check total and adjust for max mode
    total = sum(flavors)
    if total == 102:
        flavors[second_idx] -= 1
        flavors[max_idx] -= 1
    elif total == 101:
        if (max_flav - second_flav, second_idx) >= (1, max_idx):
            flavors[max_idx] -= 1
        else:
            flavors[second_idx] -= 1
            
    mildness = min_required_mildness(diffs, max_flav, second_flav, decrease_idx)

    def can_add(i: int, delta: int) -> bool:
        """Check if adding delta to flavors[i] maintains all constraints."""
        total = sum(flavors)
        if total + delta > 100 or flavors[i] % (delta * 2) == 0 or flavors[i] > 61:
            return False
        second_idx = sorted(range(5), key=lambda j: (flavors[j], -j))[-2]
        decrease = weakest_penalty(flavors, max_idx, second_idx, mildness, delta)
        if i in (max_idx, second_idx) and decrease > -diffs[decrease_idx]:
            return False
        if i != max_idx and (flavors[i] + delta, max_idx) > (flavors[max_idx], i):
            return False
        return i in (max_idx, second_idx) or (
            (flavors[i] + delta, second_idx) <= (flavors[second_idx], i)
        )

    # Prefer even values (+1) and multiples of 4 (+2)
    for delta in (1, 2, 1, 2):
        for i in range(5):
            if can_add(i, delta):
                flavors[i] += delta

    return tuple(flavors), mildness
