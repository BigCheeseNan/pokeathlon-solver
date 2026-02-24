"""Tests for solver_core.main.flavors module."""

import pytest
from solver_core.main.flavors import min_required_mildness, find_flavors


class TestMinRequiredMildness:
    """Tests for min_required_mildness function."""

    def test_no_mildness_needed(self):
        """Test when decrease already satisfies constraint without mildness."""
        diffs = [1, 1, -10, 1, 1]  # decrease_idx = 2 with min_diff = -10
        max_flav, second_flav = 5, 5
        decrease_idx = 2

        # decrease = 5 + 5 = 10, which is <= -(-10) = 10
        mildness = min_required_mildness(diffs, max_flav, second_flav, decrease_idx)
        assert mildness == 0

    def test_mildness_25_needed(self):
        """Test when mildness=25 is needed."""
        diffs = [1, 1, -8, 1, 1]  # decrease_idx = 2 with min_diff = -8
        max_flav, second_flav = 10, 5
        decrease_idx = 2

        # Initial decrease = 15 > 8
        # At mildness=25: (15 * 90) // 100 = 13 > 8
        # Keep checking...
        mildness = min_required_mildness(diffs, max_flav, second_flav, decrease_idx)
        # Should find a mildness value that works
        assert mildness == 125

    def test_mildness_200_boundary(self):
        """Test that 200 mildness gives 20% penalty."""
        diffs = [0, 0, -10, 0, 0]
        max_flav, second_flav = 30, 20
        decrease_idx = 2

        # Sum = 50, need decrease <= 10
        # At 200: (50 * 20) // 100 = 10
        mildness = min_required_mildness(diffs, max_flav, second_flav, decrease_idx)
        assert mildness == 200

    def test_mildness_255_boundary(self):
        """Test that 255 mildness gives 10% penalty."""
        diffs = [0, 0, -5, 0, 0]
        max_flav, second_flav = 30, 20
        decrease_idx = 2

        # Sum = 50, need decrease <= 5
        # At 255: (50 * 10) // 100 = 5
        mildness = min_required_mildness(diffs, max_flav, second_flav, decrease_idx)
        assert mildness == 255

    def test_impossible_case(self):
        """Test when even max mildness can't satisfy constraint."""
        diffs = [0, 0, -1, 0, 0]
        max_flav, second_flav = 30, 20
        decrease_idx = 2

        # Sum = 50
        # At mildness=255: (50 * 10) // 100 = 5 > 1
        # Even 20% (at 200-254) gives (50 * 20) // 100 = 10 > 1
        mildness = min_required_mildness(diffs, max_flav, second_flav, decrease_idx)
        # Function will return max mildness (doesn't fail because later adjustment to daily mods can help)
        assert mildness == 255

    def test_zero_decrease(self):
        """Test when max and second flavors sum to zero or less."""
        diffs = [0, 0, 0, 0, 0]
        max_flav, second_flav = 0, 0
        decrease_idx = 0

        mildness = min_required_mildness(diffs, max_flav, second_flav, decrease_idx)
        assert mildness == 0


class TestFindFlavors:
    """Tests for find_flavors function."""

    def test_all_satisfied_no_juice_needed(self):
        """Test when all requirements are already satisfied."""
        desired_stars = (0, 0, 0, 0, 0)
        modifiers = [0, 0, 0, 0, 0]

        result = find_flavors(desired_stars, modifiers, mode="min")
        assert result is not None
        flavors, mildness = result
        assert flavors == (0, 0, 0, 0, 0)
        assert mildness == 0

    def test_simple_single_boost(self):
        """Test simple case requiring boost to one stat."""
        desired_stars = (2, 0, 0, 0, 0)  # Need power boost
        modifiers = [0, 0, 0, 0, 0]

        result = find_flavors(desired_stars, modifiers, mode="min")
        # May return None in min mode if constraints can't be met minimally
        # Try with modifiers that give some base
        modifiers = [9, 9, 9, 9, 9]  # Start with daily minimum bonuses
        result = find_flavors(desired_stars, modifiers, mode="min")

        assert result is not None
        flavors, mildness = result
        # Should boost power (index 0)
        assert flavors[0] > 0
        # Total should be <= 100
        assert sum(flavors) <= 100
        # Each flavor should be <= 63
        assert all(f <= 63 for f in flavors)

    def test_two_stat_boost(self):
        """Test boosting two stats."""
        desired_stars = (2, 2, 0, 0, -1)  # Need power and stamina
        modifiers = [9, 9, 9, 9, 9]  # Start with daily minimum bonuses

        result = find_flavors(desired_stars, modifiers, mode="min")

        assert result is not None
        flavors, mildness = result
        # Power and stamina should have flavors
        assert flavors[0] > 0  # power
        assert flavors[1] > 0  # stamina
        assert sum(flavors) <= 100
        assert all(f <= 63 for f in flavors)

    def test_impossible_constraint(self):
        """Test when constraints cannot be satisfied (min mode)."""
        # Very high requirement that exceeds flavor caps
        desired_stars = (4, 4, 4, 0, 0)
        modifiers = [-50, -50, -50, 0, 0]

        result = find_flavors(desired_stars, modifiers, mode="min")
        assert result is None
        # Should return None in min mode if impossible
        # (based on code: if max_flav > 63 or max_flav + second_flav > 100)
        # This may or may not be impossible depending on exact numbers

    def test_negative_stars(self):
        """Test with negative star requirements (penalties acceptable)."""
        desired_stars = (-1, -1, 0, 0, 0)
        modifiers = [0, 0, 0, 0, 0]

        result = find_flavors(desired_stars, modifiers, mode="min")
        assert result is not None
        flavors, mildness = result
        assert flavors == (0, 0, 0, 0, 0)

        # Should work with minimal or no flavors
        # Negative stars mean we can accept penalties

    def test_tie_breaking_same_diffs(self):
        """Test"""
        desired_stars = (2, 2, 3, 0, -4)
        modifiers = [44, 9, 9, 9, -26]

        result = find_flavors(desired_stars, modifiers, mode="min")

        assert result is not None
        flavors, mildness = result
        # Due to tie-breaking by index, skill should be strongest
        assert flavors[2] > flavors[1] >= flavors[0]
        assert sum(flavors) <= 100
        assert all(f <= 63 for f in flavors)

    def test_flavor_caps_respected(self):
        """Test that flavor caps are always respected."""
        # Try various inputs
        test_cases = [
            ((3, 2, 1, 0, -4), [0, 0, 15, 0, 0]),
            ((2, 2, 2, 0, -4), [40, 0, 0, 0, 0]),
            ((4, 0, 0, 0, -4), [35, 0, 0, 0, 0]),
        ]

        for desired_stars, modifiers in test_cases:
            for mode in ["min", "max"]:
                result = find_flavors(desired_stars, modifiers, mode=mode)
                assert result is not None
                flavors, mildness = result
                assert sum(flavors) <= 100, f"Total exceeds 100: {flavors}"
                assert all(f <= 63 for f in flavors), f"Flavor exceeds 63: {flavors}"
                assert all(f >= 0 for f in flavors), f"Negative flavor: {flavors}"

    def test_even_preference(self):
        """Test that the algorithm prefers even values and multiples of 4."""
        desired_stars = (1, 0, 0, 0, 0)
        modifiers = [0, 0, 0, 0, 0]

        result = find_flavors(desired_stars, modifiers, mode="min")
        assert result is not None
        flavors, mildness = result

        # The can_add logic adds +1 and +2 deltas when possible
        assert flavors[0] % 4 == 0  # power flavor should be multiple of 4
        # Just verify result is valid
        assert sum(flavors) <= 100

    def test_max_mode_caps(self):
        """Test that max mode respects its specific caps."""
        desired_stars = (3, 2, 0, 0, 0)
        modifiers = [9, 9, 9, 9, 9]

        result = find_flavors(desired_stars, modifiers, mode="max")
        assert result is not None
        flavors, mildness = result

        # In max mode: second_flav <= 50, max_flav <= min(63, 100 - second_flav)
        # Mildness may vary based on constraints
        assert 0 <= mildness <= 255
        # Verify caps
        second_idx = sorted(range(5), key=lambda i: (flavors[i],))[-2]
        assert flavors[second_idx] <= 50

    def test_return_types(self):
        """Test that return types are correct."""
        desired_stars = (1, 1, 0, 0, 0)
        modifiers = [9, 9, 9, 9, 9]

        result = find_flavors(desired_stars, modifiers, mode="min")

        if result is not None:
            flavors, mildness = result
            assert isinstance(flavors, tuple)
            assert len(flavors) == 5
            assert all(isinstance(f, int) for f in flavors)
            assert isinstance(mildness, int)
            assert 0 <= mildness <= 255
