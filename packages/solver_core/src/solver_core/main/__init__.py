"""Core solver logic."""

from .solution import find_all_solutions, Solution
from .modifiers import (
    star_to_min_modifier,
    apply_nature_effect,
    apply_recipe_effect,
    required_daily_modifiers,
)
from .flavors import find_flavors
from .utils import (
    clamp_daily_requirement,
    pokemon_to_star_diffs,
    reorder_speed_to_stat_flavor,
    reorder_stat_flavor_to_speed,
    weakest_penalty,
)

__all__ = [
    "find_all_solutions",
    "Solution",
    "star_to_min_modifier",
    "apply_nature_effect",
    "apply_recipe_effect",
    "required_daily_modifiers",
    "find_flavors",
    "clamp_daily_requirement",
    "pokemon_to_star_diffs",
    "reorder_speed_to_stat_flavor",
    "reorder_stat_flavor_to_speed",
    "weakest_penalty",
]
