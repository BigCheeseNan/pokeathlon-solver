"""
Pokeathlon Pokemon Finder Library

This library provides utilities to find Pokemon that meet specific stat requirements
for Pokeathlon courses based on their base stats and maximum potential stats.

Stat categories:
- Speed: Hurdle Dash, Pennant Capture, and Relay Run
- Power: Block Smash, Circle Push, and Goal Roll
- Skill: Snow Throw, Goal Roll, and Pennant Capture
- Stamina: Ring Drop, Relay Run, and Block Smash
- Jump: Lamp Jump, Disc Catch, and Hurdle Dash
"""

import json
import os
from dataclasses import fields
from typing import Optional
from solver_core.constants import PokeathlonStats, intup


def from_dict(data: dict) -> PokeathlonStats:
    """Convert a dictionary to a PokeathlonStats object."""
    allowed = {f.name for f in fields(PokeathlonStats)}
    filtered = {k: v for k, v in data.items() if k in allowed}
    return PokeathlonStats(**filtered)


def load_pokemon_data(file_path: Optional[str] = None) -> list[PokeathlonStats]:
    """
    Load Pokemon data from a JSON file.

    Args:
        file_path: Path to the JSON file. If None, uses pokeathlon_stats_full.json in the same directory.

    Returns:
        List of PokeathlonStats objects.
    """
    if file_path is None:
        file_path = os.path.join(
            os.path.dirname(__file__), "pokeathlon_stats_full.json"
        )

    with open(file_path, "r") as f:
        raw = json.load(f)

    return [from_dict(item) for item in raw]


def can_meet_min_stats(stats: intup, stat_max: intup, min_stats: intup) -> bool:
    """
    Check if a Pokemon can meet the minimum stat requirements.

    Args:
        stats: Current base stats (speed, power, skill, stamina, jump)
        stat_max: Maximum potential stats (speed, power, skill, stamina, jump)
        min_stats: Minimum required stats (speed, power, skill, stamina, jump)

    Returns:
        True if the Pokemon can meet the requirements, False otherwise.
    """
    positive_count = 0
    total_needed = 0
    max_needed = 0
    count_4 = 0

    for i in range(5):
        if stat_max[i] < min_stats[i]:
            return False

        needed = min_stats[i] - stats[i]
        if needed > 0:
            positive_count += 1
            total_needed += needed
            max_needed = max(max_needed, needed)

            if needed == 4:
                count_4 += 1
                if count_4 > 1:
                    return False

            if positive_count > 3 or total_needed > 8:
                return False

    if max_needed == 4 and positive_count > 2:
        return False

    return True


def find_lowest_total_pokemon(
    min_stats: intup,
    pokemon_data: Optional[list[PokeathlonStats]] = None,
    top_n: int = 10,
    data_file: Optional[str] = None,
) -> list[PokeathlonStats]:
    """
    Find Pokemon with the lowest total stats that can meet minimum stat requirements.

    Args:
        min_stats: Minimum required stats (speed, power, skill, stamina, jump)
        pokemon_data: List of PokeathlonStats. If None, loads from data_file.
        top_n: Number of top results to return (default: 10)
        data_file: Path to JSON data file (used if pokemon_data is None)

    Returns:
        List of PokeathlonStats objects sorted by total stats (ascending).
    """
    if pokemon_data is None:
        pokemon_data = load_pokemon_data(data_file)

    filtered: list[PokeathlonStats] = []
    for poke in pokemon_data:
        stats = (poke.speed, poke.power, poke.skill, poke.stamina, poke.jump)
        stat_max = (
            poke.speedMax,
            poke.powerMax,
            poke.skillMax,
            poke.staminaMax,
            poke.jumpMax,
        )
        if can_meet_min_stats(stats, stat_max, min_stats):
            filtered.append(poke)

    # Sort by 'total' ascending
    filtered.sort(key=lambda x: x.total)

    # Get the top_n with the lowest total
    return filtered[:top_n]


def print_pokemon_stats(pokemon: PokeathlonStats) -> None:
    """Print formatted stats for a single Pokemon."""
    print(
        f"Name: {pokemon.name}, Total: {pokemon.total}, Stats: \n"
        f"speed={pokemon.speed} power={pokemon.power} skill={pokemon.skill} "
        f"stamina={pokemon.stamina} jump={pokemon.jump}\n"
        f"speMa={pokemon.speedMax} powMa={pokemon.powerMax} skiMa={pokemon.skillMax} "
        f"stamMax={pokemon.staminaMax} juMa={pokemon.jumpMax}"
    )


# Example minimum stat configurations for different courses
# Format: (speed, power, skill, stamina, jump)
COURSE_PRESETS = {
    "stamina_psyduck": (5, 5, 4, 2, 1),
    "stamina_magikarp": (5, 1, 1, 4, 1),
    "speed_magikarp": (5, 1, 1, 4, 1),
    "speed_sunkern": (5, 1, 1, 4, 4),
    "power_psyduck": (1, 5, 4, 2, 1),
    "power_burmy_stamina": (4, 1, 4, 3, 1),
    "power_burmy_skill": (4, 1, 5, 1, 1),
    "power_sunkern": (5, 1, 4, 4, 1),
    "skill_burmy_stamina": (4, 1, 4, 3, 1),
    "skill_burmy_speed": (5, 1, 4, 1, 1),
    "skill_sunkern": (5, 1, 4, 4, 1),
    "skill_psyduck": (5, 1, 5, 4, 1),
    "jump_sunkern": (5, 4, 1, 1, 5),
    "jump_magikarp": (5, 1, 1, 1, 4),
    "wildcard": (5, 5, 4, 4, 5),
}


if __name__ == "__main__":

    # Speed		Hurdle Dash, Pennant Capture, and Relay Run
    # Power		Block Smash, Circle Push, and Goal Roll
    # Skill		Snow Throw, Goal Roll, and Pennant Capture
    # Stamina	Ring Drop, Relay Run, and Block Smash
    # Jump		Lamp Jump, Disc Catch, and Hurdle Dash

    # Set the minimum stat requirements here
    # speed, power, skill, stamina, jump
    MIN_STATS = (5, 5, 4, 2, 1)  # stamina course (psyduck)
    MIN_STATS = (5, 5, 2, 4, 1)  # stamina course (psyduck) !!
    MIN_STATS = (5, 1, 1, 4, 1)  # stamina course (magikarp) !
    MIN_STATS = (5, 1, 1, 4, 1)  # speed course (magikarp: 2 jump) !!!
    MIN_STATS = (5, 1, 1, 4, 4)  # speed course (sunkern: 4/5 jump)
    MIN_STATS = (1, 5, 4, 2, 1)  # power course (psyduck) !!
    MIN_STATS = (4, 1, 4, 3, 1)  # power course (plant cloak burmy: stamina focus) !
    MIN_STATS = (4, 1, 5, 1, 1)  # power course (plant cloak burmy: skill focus)
    MIN_STATS = (5, 1, 4, 4, 1)  # power course (sunkern: stamina focus)
    MIN_STATS = (4, 1, 4, 3, 1)  # skill course (plant cloak burmy: stamina focus)
    MIN_STATS = (5, 1, 4, 1, 1)  # skill course (plant cloak burmy: speed focus) ?
    MIN_STATS = (5, 1, 4, 4, 1)  # skill course (sunkern: stamina focus) !!!
    MIN_STATS = (5, 1, 5, 4, 1)  # skill course (psyduck)
    MIN_STATS = (5, 4, 1, 1, 5)  # jump course (sunkern) !!!
    MIN_STATS = (5, 1, 1, 1, 4)  # jump course (magikarp)
    MIN_STATS = (5, 5, 4, 4, 5)  # wildcard

    results = find_lowest_total_pokemon(MIN_STATS, top_n=10)

    print(f"Found {len(results)} Pokemon matching criteria:\n")
    for poke in results:
        print_pokemon_stats(poke)
        print()
