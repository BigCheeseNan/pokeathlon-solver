"""Tests for solver_core.main.utils module."""

import pytest
from solver_core.main.utils import (
    reorder_speed_to_stat_flavor,
    pokemon_to_star_diffs,
    weakest_penalty,
    clamp_daily_requirement,
    NATURE_TO_INDEX,
)
from solver_core.constants import NATURES, PokeathlonStats


class TestReorderSpeedToStatFlavor:
    """Tests for reorder_speed_to_stat_flavor function."""

    def test_basic_reordering(self):
        """Test that reordering works correctly."""
        # Input: (speed, power, skill, stamina, jump)
        # Output: (power, stamina, skill, jump, speed)
        input_tuple = (5, 4, 3, 2, 1)
        result = reorder_speed_to_stat_flavor(input_tuple)
        assert result == (4, 2, 3, 1, 5)

    def test_all_same_values(self):
        """Test with all identical values."""
        input_tuple = (3, 3, 3, 3, 3)
        result = reorder_speed_to_stat_flavor(input_tuple)
        assert result == (3, 3, 3, 3, 3)

    def test_negative_values(self):
        """Test with negative values."""
        input_tuple = (-1, -2, -3, -4, -5)
        result = reorder_speed_to_stat_flavor(input_tuple)
        assert result == (-2, -4, -3, -5, -1)

    def test_idempotency_check(self):
        """Test that applying twice gets back to different order."""
        input_tuple = (1, 2, 3, 4, 5)
        once = reorder_speed_to_stat_flavor(input_tuple)
        twice = reorder_speed_to_stat_flavor(once)
        # Should not be the same as input
        assert once != input_tuple
        # Double application should give different result
        assert twice != input_tuple


class TestPokemonToStarDiffs:
    """Tests for pokemon_to_star_diffs function."""

    def test_basic_diff_calculation(self):
        """Test basic star difference calculation."""
        desired = (3, 4, 2, 3, 1)  # speed, power, skill, stamina, jump
        pokemon = PokeathlonStats(
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
        
        # Expected diffs (in STAT_FLAVOR order: power, stamina, skill, jump, speed):
        # power: 4 - 3 = 1
        # stamina: 3 - 2 = 1
        # skill: 2 - 2 = 0
        # jump: desired=1, min=1, so -4 (relaxation applies)
        # speed: 3 - 2 = 1
        result = pokemon_to_star_diffs(desired, pokemon)
        assert result == (1, 1, 0, -4, 1)

    def test_min_stat_relaxation(self):
        """Test that desired <= min_stat results in -4 diff."""
        desired = (1, 4, 2, 3, 1)  # speed=1 is at/below min
        pokemon = PokeathlonStats(
            id=1,
            dex_id="001",
            name="Test",
            speed=2,
            power=3,
            skill=2,
            stamina=2,
            jump=2,
            speedMin=2,  # min >= desired for speed
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
        
        result = pokemon_to_star_diffs(desired, pokemon)
        # speed diff should be -4 (unconstrained) since desired <= min
        assert result[4] == -4  # speed is last in STAT_FLAVOR order

    def test_all_min_stats(self):
        """Test when all desired values are at minimum."""
        desired = (1, 1, 1, 1, 1)
        pokemon = PokeathlonStats(
            id=1,
            dex_id="001",
            name="Test",
            speed=3,
            power=3,
            skill=3,
            stamina=3,
            jump=3,
            speedMin=1,
            powerMin=1,
            skillMin=1,
            staminaMin=1,
            jumpMin=1,
            speedMax=4,
            powerMax=4,
            skillMax=4,
            staminaMax=4,
            jumpMax=4,
            total=15,
        )
        
        result = pokemon_to_star_diffs(desired, pokemon)
        # All should be -4 since desired == min
        assert result == (-4, -4, -4, -4, -4)

    def test_max_desired_stars(self):
        """Test with maximum desired stars."""
        desired = (5, 5, 5, 5, 5)
        pokemon = PokeathlonStats(
            id=1,
            dex_id="001",
            name="Test",
            speed=2,
            power=2,
            skill=2,
            stamina=2,
            jump=2,
            speedMin=1,
            powerMin=1,
            skillMin=1,
            staminaMin=1,
            jumpMin=1,
            speedMax=5,
            powerMax=5,
            skillMax=5,
            staminaMax=5,
            jumpMax=5,
            total=10,
        )
        
        result = pokemon_to_star_diffs(desired, pokemon)
        # All should need +3 (5 - 2)
        assert result == (3, 3, 3, 3, 3)


class TestWeakestPenalty:
    """Tests for weakest_penalty function."""

    def test_zero_mildness_full_penalty(self):
        """Test that mildness=0 gives 100% penalty."""
        flavs = [40, 20, 0, 0, 0]
        primary, secondary = 0, 1
        penalty = weakest_penalty(flavs, primary, secondary, mildness=0)
        # Sum = 40 + 20 = 60, 100% = 60
        assert penalty == 60

    def test_mildness_25(self):
        """Test mildness=25 gives 90% penalty."""
        flavs = [40, 20, 0, 0, 0]
        primary, secondary = 0, 1
        penalty = weakest_penalty(flavs, primary, secondary, mildness=25)
        # Sum = 60, (60 * 90) // 100 = 54
        assert penalty == 54

    def test_mildness_100(self):
        """Test mildness=100 gives 60% penalty."""
        flavs = [50, 30, 0, 0, 0]
        primary, secondary = 0, 1
        penalty = weakest_penalty(flavs, primary, secondary, mildness=100)
        # Sum = 80, (80 * 60) // 100 = 48
        assert penalty == 48

    def test_mildness_200(self):
        """Test mildness=200-254 gives 20% penalty."""
        flavs = [50, 50, 0, 0, 0]
        primary, secondary = 0, 1
        penalty = weakest_penalty(flavs, primary, secondary, mildness=200)
        # Sum = 100, (100 * 20) // 100 = 20
        assert penalty == 20

    def test_mildness_255(self):
        """Test mildness=255 gives 10% penalty."""
        flavs = [50, 50, 0, 0, 0]
        primary, secondary = 0, 1
        penalty = weakest_penalty(flavs, primary, secondary, mildness=255)
        # Sum = 100, (100 * 10) // 100 = 10
        assert penalty == 10

    def test_integer_division_rounding(self):
        """Test that integer division rounds down correctly."""
        flavs = [33, 22, 0, 0, 0]
        primary, secondary = 0, 1
        penalty = weakest_penalty(flavs, primary, secondary, mildness=0)
        # Sum = 55, should be 55 (not 55.0)
        assert penalty == 55
        assert isinstance(penalty, int)

    def test_different_primary_secondary_order(self):
        """Test that order of primary/secondary doesn't matter for sum."""
        flavs = [30, 20, 10, 5, 1]
        penalty1 = weakest_penalty(flavs, 0, 1, mildness=0)
        penalty2 = weakest_penalty(flavs, 1, 0, mildness=0)
        # Both should give same result: 30 + 20 = 50
        assert penalty1 == penalty2 == 50


class TestClampDailyRequirement:
    """Tests for clamp_daily_requirement function."""

    def test_already_odd_within_range(self):
        """Test values that are already odd and within range."""
        assert clamp_daily_requirement(5) == 5
        assert clamp_daily_requirement(-7) == -7
        assert clamp_daily_requirement(1) == 1
        assert clamp_daily_requirement(-1) == -1

    def test_even_values_rounded_up(self):
        """Test that even values are rounded up to next odd."""
        assert clamp_daily_requirement(4) == 5
        assert clamp_daily_requirement(0) == 1
        assert clamp_daily_requirement(-6) == -5
        assert clamp_daily_requirement(-2) == -1

    def test_below_minimum(self):
        """Test values below -9 are clamped to -9."""
        assert clamp_daily_requirement(-15) == -9
        assert clamp_daily_requirement(-100) == -9
        assert clamp_daily_requirement(-10) == -9

    def test_above_maximum(self):
        """Test values above 9 return None."""
        assert clamp_daily_requirement(10) is None
        assert clamp_daily_requirement(15) is None
        assert clamp_daily_requirement(100) is None

    def test_boundary_values(self):
        """Test boundary values."""
        assert clamp_daily_requirement(9) == 9
        assert clamp_daily_requirement(-9) == -9
        assert clamp_daily_requirement(8) == 9  # Even, rounds up to 9
        assert clamp_daily_requirement(-8) == -7  # Even, rounds up to -7

    def test_maximum_impossible(self):
        """Test that 10 (which would round to 11) is impossible."""
        assert clamp_daily_requirement(10) is None


class TestNatureToIndex:
    """Tests for NATURE_TO_INDEX mapping."""

    def test_all_natures_mapped(self):
        """Test that all 25 natures are in the mapping."""
        assert len(NATURE_TO_INDEX) == 25

    def test_indices_are_sequential(self):
        """Test that indices are 0-24."""
        indices = set(NATURE_TO_INDEX.values())
        assert indices == set(range(25))

    def test_mapping_matches_natures_list(self):
        """Test that mapping corresponds to NATURES list order."""
        for idx, nature in enumerate(NATURES):
            assert NATURE_TO_INDEX[nature] == idx

    def test_sample_nature_lookups(self):
        """Test looking up specific natures."""
        # Hardy should be first (index 0)
        hardy = ("Hardy", 0, 4, True)
        assert NATURE_TO_INDEX[hardy] == 0
        
        # Find a non-neutral nature
        adamant = ("Adamant", 0, 3, False)
        assert adamant in NATURE_TO_INDEX
        assert isinstance(NATURE_TO_INDEX[adamant], int)
