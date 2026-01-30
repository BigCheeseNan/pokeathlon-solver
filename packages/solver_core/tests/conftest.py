"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_pokemon_stats():
    """Sample Pokemon stats for testing."""
    from solver_core.constants import PokeathlonStats
    
    return PokeathlonStats(
        id=1,
        dex_id="001",
        name="Bulbasaur",
        speed=2,
        power=3,
        skill=2,
        stamina=2,
        jump=2,
        speedMin=1,
        powerMin=2,
        skillMin=1,
        staminaMin=1,
        jumpMin=1,
        speedMax=3,
        powerMax=4,
        skillMax=3,
        staminaMax=3,
        jumpMax=3,
        total=11,
    )


@pytest.fixture
def sample_natures():
    """Sample natures for testing."""
    return [
        ("Hardy", 0, 4, True),      # Neutral
        ("Adamant", 0, 2, False),   # +Power, -Skill
        ("Bold", 1, 0, False),      # +Stamina, -Power
        ("Timid", 4, 0, False),     # +Speed, -Power
    ]
