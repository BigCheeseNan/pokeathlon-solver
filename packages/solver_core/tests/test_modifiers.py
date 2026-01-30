"""Tests for solver_core.main.modifiers module."""

import pytest
from solver_core.main import (
    star_to_min_modifier,
    apply_nature_effect,
    apply_recipe_effect,
    required_daily_modifiers,
)


class TestStarToMinModifier:
    """Tests for star_to_min_modifier function."""

    def test_valid_star_bonuses(self):
        """Test conversion of all valid star bonuses."""
        # Mapping based on the function implementation
        expected = {
            -4: -(10**9),
            -3: -119,
            -2: -79,
            -1: -39,
            0: -14,
            1: 15,
            2: 40,
            3: 80,
            4: 120,
        }
        for star, expected_mod in expected.items():
            assert star_to_min_modifier(star) == expected_mod

    def test_invalid_star_bonus_too_low(self):
        """Test that values below -4 raise ValueError."""
        with pytest.raises(ValueError, match="Star bonus must be in"):
            star_to_min_modifier(-5)

    def test_invalid_star_bonus_too_high(self):
        """Test that values above 4 raise ValueError."""
        with pytest.raises(ValueError, match="Star bonus must be in"):
            star_to_min_modifier(5)


class TestApplyNatureEffect:
    """Tests for apply_nature_effect function."""

    def test_neutral_nature(self):
        """Test neutral nature applies +10/-10."""
        # Hardy: +power, -speed, neutral
        nature = ("Hardy", 0, 4, True)
        effect = apply_nature_effect(nature)
        assert effect == [10, 0, 0, 0, -10]

    def test_non_neutral_nature(self):
        """Test non-neutral nature applies +35/-35."""
        # Adamant: +power, -skill, non-neutral
        nature = ("Adamant", 0, 2, False)
        effect = apply_nature_effect(nature)
        assert effect == [35, 0, -35, 0, 0]

    def test_same_index_neutral(self):
        """Test nature with same plus/minus index (neutral variant)."""
        # Docile: +stamina, -skill, neutral
        nature = ("Docile", 1, 3, True)
        effect = apply_nature_effect(nature)
        assert effect == [0, 10, 0, -10, 0]

    def test_all_stat_combinations(self):
        """Test that effect list always has 5 elements and correct positions."""
        for plus_idx in range(5):
            for minus_idx in range(5):
                for is_neutral in [True, False]:
                    nature = ("Test", plus_idx, minus_idx, is_neutral)
                    effect = apply_nature_effect(nature)
                    assert len(effect) == 5
                    delta = 10 if is_neutral else 35
                    # When plus and minus are same index, they cancel out
                    if plus_idx == minus_idx:
                        assert effect[plus_idx] == 0
                    else:
                        assert effect[plus_idx] == delta
                        assert effect[minus_idx] == -delta


class TestApplyRecipeEffect:
    """Tests for apply_recipe_effect function."""

    def test_all_zero_flavors(self):
        """Test that all-zero flavors produce all-zero effects."""
        flavors = (0, 0, 0, 0, 0)
        effect = apply_recipe_effect(flavors)
        assert effect == [0, 0, 0, 0, 0]

    def test_single_dominant_flavor(self):
        """Test recipe with one strong flavor."""
        # Power = 50, rest = 0
        flavors = (50, 0, 0, 0, 0)
        effect = apply_recipe_effect(flavors)
        # Strongest: floor(1.5 * 50) + 10 = 75 + 10 = 85
        # Second strongest: any of the zeros, gets 0
        # Weakest: gets -(50 + 0) = -50 (one of the remaining zeros)
        assert effect[0] == 85  # power gets strongest bonus
        # One of the other indices should have -50
        assert effect[4] == -50  # speed gets weakest penalty

    def test_two_equal_flavors(self):
        """Test tie-breaking when two flavors are equal."""
        # Power and stamina both 30, rest 0
        flavors = (30, 30, 1, 0, 1)
        effect = apply_recipe_effect(flavors)
        # When tied, max() picks the first occurrence
        # So power (index 0) is strongest: floor(1.5 * 30) + 10 = 55
        # Stamina (index 1) is second strongest: floor(1.5 * 30) = 45
        # Speed (index 4) is weakest: -(30 + 30) = -60
        assert effect[0] == 55  # floor(1.5 * 30) + 10 = 45 + 10
        assert effect[1] == 45  # floor(1.5 * 30)
        assert effect[3] == -60  # -(30 + 30)

    def test_with_mildness(self):
        """Test that mildness affects the weakest penalty."""
        flavors = (40, 20, 0, 0, 0)
        
        # Mildness = 0: penalty = 100% of sum = 60
        effect_0 = apply_recipe_effect(flavors, mildness=0)
        # Mildness = 100: penalty = 60% of sum = (60 * 60) // 100 = 36
        effect_100 = apply_recipe_effect(flavors, mildness=100)
        # Mildness = 255: penalty = 10% of sum = (60 * 10) // 100 = 6
        effect_255 = apply_recipe_effect(flavors, mildness=255)
        
        # Weakest penalty should decrease with mildness
        assert abs(effect_0[4]) > abs(effect_100[4]) > abs(effect_255[4])

    def test_realistic_recipe(self):
        """Test a realistic recipe configuration."""
        flavors = (35, 20, 0, 1, 1)
        effect = apply_recipe_effect(flavors)
        
        # Strongest: power (35) -> floor(1.5 * 35) + 10 = 52 + 10 = 62
        assert effect[0] == 62
        # Second: stamina (20) -> floor(1.5 * 20) = 30
        assert effect[1] == 30
        # Weakest: speed (0) -> -(35 + 20) = -55
        assert effect[2] == -55


class TestRequiredDailyModifiers:
    """Tests for required_daily_modifiers function."""

    def test_all_requirements_met(self):
        """Test when base modifiers already meet star requirements."""
        desired_stars = (1, 1, 1, 1, 1)  # All need >= 15
        base_modifiers = [20, 20, 20, 20, 20]  # All already above 15
        
        result = required_daily_modifiers(desired_stars, base_modifiers)
        # Need >= (15 - 20) = -5 for each, clamped to odd: -5
        assert result == (-5, -5, -5, -5, -5)

    def test_needs_positive_daily(self):
        """Test when positive daily modifiers are needed."""
        desired_stars = (2, 2, 2, 2, 2)  # All need >= 40
        base_modifiers = [35, 35, 35, 35, 35]  # All need +5
        
        result = required_daily_modifiers(desired_stars, base_modifiers)
        # Need >= 5, so clamp to odd value >= 5, which is 5
        assert result == (5, 5, 5, 5, 5)

    def test_needs_even_value_rounds_up(self):
        """Test that even requirements are rounded up to next odd."""
        desired_stars = (1, 1, 1, 1, 1)  # All need >= 15
        base_modifiers = [10, 10, 10, 10, 10]  # All need +5 (already odd)
        
        result = required_daily_modifiers(desired_stars, base_modifiers)
        assert result == (5, 5, 5, 5, 5)
        
        # Now test with even requirement
        base_modifiers = [11, 11, 11, 11, 11]  # All need +4 -> rounds to +5
        result = required_daily_modifiers(desired_stars, base_modifiers)
        assert result == (5, 5, 5, 5, 5)

    def test_impossible_requirement(self):
        """Test that impossible requirements (>9) return None."""
        desired_stars = (4, 1, 1, 1, 1)  # First needs >= 120
        base_modifiers = [100, 20, 20, 20, 20]  # First needs +20 (> 9)
        
        result = required_daily_modifiers(desired_stars, base_modifiers)
        assert result is None

    def test_negative_daily_required(self):
        """Test when negative daily modifiers are needed."""
        desired_stars = (-2, -2, -2, -2, -2)  # All need >= -79
        base_modifiers = [-100, -100, -100, -100, -100]  # All need +21
        
        result = required_daily_modifiers(desired_stars, base_modifiers)
        # Need >= 21, but that's > 9, so impossible
        assert result is None
        
        # Test achievable negative case
        desired_stars = (-3, -3, -3, -3, -3)  # All need >= -119
        base_modifiers = [-120, -120, -120, -100, -100]  # Already sufficient
        result = required_daily_modifiers(desired_stars, base_modifiers)
        assert result == (1, 1, 1, -9, -9)

    def test_mixed_requirements(self):
        """Test with mixed positive and negative requirements."""
        desired_stars = (3, 1, 0, -1, -2)
        base_modifiers = [75, 10, -10, -35, -75]
        
        result = required_daily_modifiers(desired_stars, base_modifiers)
        # 3: needs >= 80, has 75 -> need 5
        # 1: needs >= 15, has 10 -> need 5
        # 0: needs >= -14, has -10 -> need (-14 - (-10)) = -4 -> -3 (odd)
        # -1: needs >= -39, has -35 -> need (-39 - (-35)) = -4 -> -3 (odd)
        # -2: needs >= -79, has -75 -> need (-79 - (-75)) = -4 -> -3 (odd)
        assert result == (5, 5, -3, -3, -3)
