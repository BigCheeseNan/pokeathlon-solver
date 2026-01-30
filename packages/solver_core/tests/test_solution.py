"""Tests for solver_core.main.solution module."""

import pytest
from solver_core.main import find_all_solutions
from solver_core.constants import Solution, NATURES, NATURE_TO_INDEX


class TestFindAllSolutions:
    """Tests for find_all_solutions function."""

    def test_all_zero_stars(self):
        """Test with no stat bonuses needed."""
        desired_stars = (0, 0, 0, 0, 0)
        results = find_all_solutions(desired_stars, mode="min")
        
        # Should find solutions (no aprijuice needed)
        assert len(results) > 0
        # All solutions should have zero or minimal flavors
        for sol in results:
            assert isinstance(sol, Solution)
            assert sum(sol.flavors) <= 100

    def test_single_stat_boost(self):
        """Test boosting a single stat."""
        desired_stars = (2, 0, 0, 0, 0)  # Power +2
        results = find_all_solutions(desired_stars, mode="min")
        
        assert len(results) > 0
        # Check that solutions are valid
        for sol in results:
            assert isinstance(sol, Solution)
            assert sol.nature in NATURES
            assert len(sol.flavors) == 5
            assert len(sol.required_daily) == 5
            # All required daily mods should be odd and in range
            for daily in sol.required_daily:
                assert daily % 2 != 0  # odd
                assert -9 <= daily <= 9

    def test_multiple_stat_boosts(self):
        """Test boosting multiple stats."""
        desired_stars = (2, 1, 1, 0, 0)
        results = find_all_solutions(desired_stars, mode="min")
        
        assert len(results) > 0
        # Verify solution structure
        for sol in results:
            assert len(sol.nature) == 4  # (name, plus_idx, minus_idx, is_neutral)
            assert len(sol.recipe_effect) == 5
            assert len(sol.nature_effect) == 5

    def test_impossible_too_many_positive_stars(self):
        """Test constraint: max 3 stats with positive bonuses."""
        desired_stars = (1, 1, 1, 1, 0)  # 4 positive stats
        results = find_all_solutions(desired_stars, mode="min")
        
        # Should return empty list (violates len(positive_stars) > 3)
        assert results == []

    def test_impossible_multiple_4_stars(self):
        """Test constraint: at most one stat can have +4 bonus."""
        desired_stars = (4, 4, 0, 0, 0)  # Two 4-star stats
        results = find_all_solutions(desired_stars, mode="min")
        
        # Should return empty list
        assert results == []

    def test_impossible_sum_too_high(self):
        """Test constraint: sum of positive bonuses <= 8."""
        desired_stars = (3, 3, 3, 0, 0)  # Sum = 9
        results = find_all_solutions(desired_stars, mode="min")
        
        # Should return empty list
        assert results == []

    def test_4_star_requires_negative(self):
        """Test constraint: 4-star with no negatives is impossible."""
        desired_stars = (4, 0, 0, 0, 0)  # One 4-star, no negatives
        results = find_all_solutions(desired_stars, mode="min")
        
        # Should return empty list
        assert results == []

    def test_4_star_with_negative_allowed(self):
        """Test that 4-star with negative stats can work."""
        desired_stars = (4, 0, 0, -2, -2)  # One 4-star, two negatives
        results = find_all_solutions(desired_stars, mode="min")
        
        # Should find solutions (with non-neutral nature boosting power)
        # Only non-neutral natures with plus_idx=0 should work
        assert len(results) > 0
        for sol in results:
            # Nature should boost power (index 0)
            assert sol.nature[1] == 0  # plus_idx
            assert not sol.nature[3]  # non-neutral

    def test_negative_stars(self):
        """Test with negative star requirements."""
        desired_stars = (1, 0, -1, 0, 0)
        results = find_all_solutions(desired_stars, mode="min")
        
        # Should find solutions
        assert len(results) > 0

    def test_min_vs_max_mode(self):
        """Test that min and max modes produce different solutions."""
        desired_stars = (2, 1, 0, 0, -1)
        
        results_min = find_all_solutions(desired_stars, mode="min")
        results_max = find_all_solutions(desired_stars, mode="max")
        
        results_min.sort(key=lambda s: NATURE_TO_INDEX[s.nature])
        results_max.sort(key=lambda s: NATURE_TO_INDEX[s.nature])
        
        assert len(results_min) > 0
        assert len(results_max) > 0
        
        # Max mode solutions typically use higher mildness
        # but not always 255 depending on constraints
        for sol_max, sol_min in zip(results_max, results_min):
            assert sum(sol_min.flavors) <= sum(sol_max.flavors)

    def test_solution_structure(self):
        """Test that solutions have correct structure."""
        desired_stars = (1, 1, 0, 0, 0)
        results = find_all_solutions(desired_stars, mode="min")
        
        assert len(results) > 0
        sol = results[0]
        
        # Verify Solution fields
        assert hasattr(sol, 'nature')
        assert hasattr(sol, 'flavors')
        assert hasattr(sol, 'recipe_effect')
        assert hasattr(sol, 'nature_effect')
        assert hasattr(sol, 'required_daily')
        assert hasattr(sol, 'mildness')
        
        # Verify nature tuple structure
        name, plus_idx, minus_idx, is_neutral = sol.nature
        assert isinstance(name, str)
        assert 0 <= plus_idx < 5
        assert 0 <= minus_idx < 5
        assert isinstance(is_neutral, bool)

    def test_flavor_constraints(self):
        """Test that all solutions respect flavor constraints."""
        desired_stars = (3, 2, 0, 0, -4)
        results = find_all_solutions(desired_stars, mode="min")
        
        for sol in results:
            # Each flavor <= 63
            assert all(f <= 63 for f in sol.flavors)
            # Total <= 100
            assert sum(sol.flavors) <= 100
            # All non-negative
            assert all(f >= 0 for f in sol.flavors)

    def test_daily_modifier_constraints(self):
        """Test that all solutions respect daily modifier constraints."""
        desired_stars = (2, 2, 1, 0, -4)
        results = find_all_solutions(desired_stars, mode="min")
        
        assert len(results) > 0
        for sol in results:
            for daily in sol.required_daily:
                # Must be odd
                assert daily % 2 != 0
                # Must be in range
                assert -9 <= daily <= 9

    def test_edge_case_max_legal_boosts(self):
        """Test edge case with maximum legal boosts."""
        desired_stars = (3, 3, 2, 0, -4)  # Sum = 8, three positive
        results = find_all_solutions(desired_stars, mode="min")
        
        assert len(results) > 0
        # Should find some solutions
        # This is at the boundary of what's possible

    def test_all_negative_stars(self):
        """Test with all negative stars."""
        desired_stars = (-1, -1, -1, -1, -1)
        results = find_all_solutions(desired_stars, mode="min")
        
        # Should find solutions (easy case, just need penalties)
        assert len(results) > 0

    def test_mixed_positive_negative(self):
        """Test with mixed positive and negative requirements."""
        desired_stars = (2, 1, 0, -1, -2)
        results = find_all_solutions(desired_stars, mode="min")
        
        # Should find solutions
        assert len(results) > 0
        for sol in results:
            # Verify solution is structurally valid
            assert len(sol.flavors) == 5
            assert len(sol.required_daily) == 5

    def test_nature_filtering_for_4_star(self):
        """Test that only appropriate natures are used for 4-star boosts."""
        desired_stars = (4, 1, 0, 0, -4)
        results = find_all_solutions(desired_stars, mode="min")
        
        # Only non-neutral natures with plus_idx=0 should appear
        assert len(results) > 0
        for sol in results:
            assert sol.nature[1] == 0  # plus_idx must be 0 (power)
            assert not sol.nature[3]  # must be non-neutral

    def test_empty_result_cases(self):
        """Test various cases that should return empty results."""
        impossible_cases = [
            (1, 1, 1, 1, -4),  # Too many positive
            (4, 4, 0, 0, -4),  # Multiple 4-stars
            (3, 3, 3, 0, -4),  # Sum too high
            (4, 0, 0, 0, 0),  # 4-star without negative
            (2, 2, 2, 0, 0),  # min 2-star without negative
        ]
        
        for desired_stars in impossible_cases:
            results = find_all_solutions(desired_stars, mode="min")
            assert results == [], f"Expected empty for {desired_stars}, got {len(results)} results"

    def test_return_type(self):
        """Test that return type is always a list."""
        desired_stars = (1, 0, 0, 0, 0)
        results = find_all_solutions(desired_stars, mode="min")
        
        assert isinstance(results, list)
        for sol in results:
            assert isinstance(sol, Solution)

    def test_consistency_across_modes(self):
        """Test that both modes handle the same input without errors."""
        desired_stars = (2, 1, 1, 0, -3)
        
        # Both modes should work without crashing
        results_min = find_all_solutions(desired_stars, mode="min")
        results_max = find_all_solutions(desired_stars, mode="max")
        
        # Both should return lists
        assert isinstance(results_min, list)
        assert isinstance(results_max, list)
