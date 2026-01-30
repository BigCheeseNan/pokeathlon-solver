"""Shared constants for the Pokeathlon solver."""

from dataclasses import dataclass

intup = tuple[int, ...]

# Stat/flavor order used throughout the solver
# This is the API order for diffs and internal calculations
STAT_FLAVOR = ("power", "stamina", "skill", "jump", "speed")
FLAVOR_LABELS = ("spicy", "sour", "dry", "bitter", "sweet")
INGREDIENTS = ["spicy", "sour", "dry", "bitter", "sweet", "mild", "strong"]

# Alternative ordering used for some inputs (e.g., Pokemon stats from data files)
STAT_ORDER_SPEED_FIRST = ("speed", "power", "skill", "stamina", "jump")

# Recipe/flavor constraints
MAX_FLAVOR = 63
MAX_TOTAL = 100

EFFECTS: dict[str, tuple[intup, intup]] = {
    "spicy": ((4, -2, 0, 0, 0), (1, 2, 3, 4)),
    "sour": ((0, 4, -2, 0, 0), (0, 2, 3, 4)),
    "dry": ((0, 0, 4, -2, 0), (0, 1, 3, 4)),
    "bitter": ((0, 0, 0, 4, -2), (0, 1, 2, 4)),
    "sweet": ((-2, 0, 0, 0, 4), (0, 1, 2, 3)),
    "mild": ((-2, -2, -2, -2, -2), ()),
    "strong": ((2, 2, 2, 2, 2), ()),
}

# Star bonus range
MIN_STAR_BONUS = -4
MAX_STAR_BONUS = 4

# Daily modifier constraints
MIN_DAILY_MOD = -9
MAX_DAILY_MOD = 9

NATURES = [
    ("Hardy", 0, 4, True),
    ("Lonely", 0, 1, False),
    ("Brave", 0, 4, False),
    ("Adamant", 0, 3, False),
    ("Naughty", 0, 2, False),
    ("Bold", 1, 0, False),
    ("Docile", 1, 3, True),
    ("Relaxed", 1, 4, False),
    ("Impish", 1, 3, False),
    ("Lax", 1, 2, False),
    ("Timid", 4, 0, False),
    ("Hasty", 4, 1, False),
    ("Serious", 4, 2, True),
    ("Jolly", 4, 3, False),
    ("Naive", 4, 2, False),
    ("Modest", 3, 0, False),
    ("Mild", 3, 1, False),
    ("Quiet", 3, 4, False),
    ("Bashful", 3, 0, True),
    ("Rash", 3, 2, False),
    ("Calm", 2, 0, False),
    ("Gentle", 2, 1, False),
    ("Sassy", 2, 4, False),
    ("Careful", 2, 3, False),
    ("Quirky", 2, 1, True),
]

# O(1) lookup mapping for places where nature index matters
NATURE_TO_INDEX: dict[tuple[str, int, int, bool], int] = {
    nat: i for i, nat in enumerate(NATURES)
}


@dataclass
class PokeathlonStats:
    """Represents a Pokemon's Pokeathlon stats."""

    id: int
    dex_id: str
    name: str
    speed: int
    speedMax: int
    speedMin: int
    power: int
    powerMax: int
    powerMin: int
    skill: int
    skillMax: int
    skillMin: int
    stamina: int
    staminaMax: int
    staminaMin: int
    jump: int
    jumpMax: int
    jumpMin: int
    total: int


@dataclass(frozen=True)
class SeedSearchResult:
    offset: int
    x_mask: int
    num_offsets: int
    streak: int
    count: int
    pid: int
    seed: int

    @property
    def x_values(self) -> tuple[int, ...]:
        return tuple(x for x in range(1, 32) if (self.x_mask >> x) & 1)

    @property
    def natural_catch_probability(self) -> float:
        # User-provided model: num_offsets * 42950 / 0xFFFFFFFF
        return (self.num_offsets * 42950.0) / 0xFFFFFFFF


@dataclass(frozen=True)
class Solution:
    nature: tuple[str, int, int, bool]
    flavors: intup
    recipe_effect: intup
    nature_effect: intup
    required_daily: intup
    mildness: int


@dataclass(frozen=True)
class Result:
    sol: Solution
    recipe: list[str]
    grouped: list[tuple[str, int]]
    elapsed: float | None
    source: str
    ingredients: int
    daily_sum: int
    final_mods: list[int]
    seed_result: SeedSearchResult | None
