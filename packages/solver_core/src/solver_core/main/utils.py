from solver_core.constants import intup, PokeathlonStats, NATURES, ODD_INDEX, FEAS_MOD_TABLE, NATURE_TO_INDEX


def reorder_speed_to_stat_flavor(v: intup) -> intup:
    """Reorder (speed,power,skill,stamina,jump) -> (power,stamina,skill,jump,speed)."""
    speed, power, skill, stamina, jump = v
    return (power, stamina, skill, jump, speed)

def reorder_stat_flavor_to_speed(v: intup) -> intup:
    """Reorder (power,stamina,skill,jump,speed) -> (speed,power,skill,stamina,jump)."""
    power, stamina, skill, jump, speed = v
    return (speed, power, skill, stamina, jump)


def pokemon_to_star_diffs(
    desired_stars_speed_order: intup,
    pokemon: PokeathlonStats,
) -> intup:
    """Compute desired_star_diffs (STAT_FLAVOR order) from a Pokemon base statline.

    Inputs:
    - desired_stars_speed_order: (speed,power,skill,stamina,jump), each in [1..5]
    - pokemon base stats are taken from PokeathlonStats.{speed,power,skill,stamina,jump}

    Output:
    - desired_star_diffs in STAT_FLAVOR order (power,stamina,skill,jump,speed), each in [-4..4]

    Interpretation:
    We need bonuses such that base + bonus >= desired, so bonus >= (desired - base).

    Improvement using min-stats:
    Pokemon stats have a minimum (cannot be lowered below that value). If desired <= min_stat
    for a stat, then we can treat that stat as unconstrained in the bonus solver and set the
    corresponding diff to -4 ("as low as we want"). This can allow more Pokemon to match.
    """
    base = (pokemon.speed, pokemon.power, pokemon.skill, pokemon.stamina, pokemon.jump)
    mins = (
        pokemon.speedMin,
        pokemon.powerMin,
        pokemon.skillMin,
        pokemon.staminaMin,
        pokemon.jumpMin,
    )
    diffs_speed_order_list: list[int] = []
    for desired, b, mn in zip(desired_stars_speed_order, base, mins):
        if desired <= mn:
            diffs_speed_order_list.append(-4)
        else:
            diffs_speed_order_list.append(desired - b)

    diffs_speed_order = tuple(diffs_speed_order_list)
    # Validate: should be within [-4..4] given desired/base in [1..5], or -4 from min-stat relaxation.
    for x in diffs_speed_order:
        if x < -4 or x > 4:
            raise ValueError(
                "Computed star diff out of range [-4..4]; "
                f"desired={desired_stars_speed_order}, base={base}, mins={mins}, diffs={diffs_speed_order}"
            )
    return reorder_speed_to_stat_flavor(diffs_speed_order)


# O(1) mapping for places where nature index matters.
NATURE_TO_INDEX: dict[tuple[str, int, int, bool], int] = {
    nat: i for i, nat in enumerate(NATURES)
}


def weakest_penalty(flavs, primary, secondary, mildness=0) -> int:
    """The attribute corresponding to the weakest flavor is reduced by an amount depending on the mildness of the Aprijuice:
    100%, less 10% per 25 mildness (ignoring remainders) of the sum of the two strongest flavors, rounded down, if the mildness is less than 200
    20% of the sum of the two strongest flavors, rounded down, if the mildness is 200-254
    10% of the sum of the two strongest flavors, rounded down, if the mildness is 255
    """
    sum_strongest = flavs[primary] + flavs[secondary]
    if mildness < 200:
        decrease = (sum_strongest * (100 - (mildness // 25) * 10)) // 100
    elif mildness < 255:
        decrease = (sum_strongest * 20) // 100
    else:
        decrease = (sum_strongest * 10) // 100
    return decrease


def clamp_daily_requirement(x: int) -> int | None:
    """Convert a required minimum daily modifier into a valid odd int in [-9..9].

    Returns None if impossible (> 9).
    """
    if x <= -9:
        return -9
    req = x if x % 2 != 0 else x + 1
    if req > 9:
        return None
    return req

def is_feasible(nature: tuple[str, int, int, bool], power_mod: int, stamina_mod: int) -> bool:
    """Check if a given nature, power, stamina mod are achievable.

    Inputs:
    - nature: (name, primary_flavor, secondary_flavor, is_neutral)
    - power_mod: int in [-9..9]
    - stamina_mod: int in [-9..9]

    Output:
    - True if feasible, False if infeasible
    """
    nat = NATURE_TO_INDEX[nature]
    p = ODD_INDEX[power_mod]
    s = ODD_INDEX[stamina_mod]
    return (FEAS_MOD_TABLE[nat][p] >> s) & 1 == 1

if __name__ == "__main__":
    # Simple test
    nat = NATURES[0]  # Hardy
    print(is_feasible(nat, 1, -1))  # Expected: True
    print(is_feasible(nat, -9, -9)) # Expected: True
    print(is_feasible(nat, 5, 5))   # Expected: True
    print(is_feasible(nat, 9, 9))   # Expected: False
    print(is_feasible(nat, 7, 5))   # Expected: False
    print(is_feasible(nat, 5, 7))   # Expected: False
    print(is_feasible(nat, 9, -9))   # Expected: False
    print(is_feasible(nat, -9, 9))   # Expected: True
    print(is_feasible(nat, 7, -9))   # Expected: False
    print(is_feasible(nat, 5, 9))   # Expected: False
    
    rows = []
    for pow_mod in range(-9, 10, 2):
        row = []
        for stam_mod in range(-9, 10, 2):
            row.append('T' if is_feasible(nat, pow_mod, stam_mod) else 'F')
        rows.append(' '.join(row))
    print('\n'.join(rows))
    