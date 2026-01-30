"""Comprehensive fuzz/property-based tests for solution validation.

This module tests the solution-finding algorithm across a wide range of
star configurations to ensure correctness, constraint satisfaction, and
edge case handling.
"""

import pytest
from itertools import permutations, product
from typing import Iterable

from solver_core.main import (
    find_all_solutions,
    apply_recipe_effect,
    apply_nature_effect,
    star_to_min_modifier,
)
from solver_core.constants import intup, STAT_FLAVOR, Solution


# Helper functions
def is_odd_in_range(v: int, lo: int, hi: int) -> bool:
    """Check if value is odd and within range."""
    return (lo <= v <= hi) and (v % 2 != 0)


def validate_solution(stars: intup, sol: Solution) -> list[str]:
    """Validate a solution against all constraints.
    
    Returns a list of error messages (empty if valid).
    """
    errors: list[str] = []

    # Validate star domain
    if any(s < -4 or s > 4 for s in stars):
        errors.append("stars out of range [-4..4]")

    # Validate daily modifiers constraints
    if len(sol.required_daily) != 5:
        errors.append("required_daily not length 5")
    else:
        for v in sol.required_daily:
            if not is_odd_in_range(v, -9, 9):
                errors.append(
                    f"required_daily has invalid value {v} (must be odd in [-9..9])"
                )
                break

    # Validate flavors constraints (hard caps)
    if len(sol.flavors) != 5:
        errors.append("flavors not length 5")
    else:
        if any(f < 0 for f in sol.flavors):
            errors.append("flavors has negative entries")
        if any(f > 63 for f in sol.flavors):
            errors.append("flavors exceeds per-flavor cap 63")
        if sum(sol.flavors) > 100:
            errors.append("flavors exceeds total cap 100")

    # Check effects are consistent with helpers
    expected_recipe = tuple(apply_recipe_effect(sol.flavors, sol.mildness))
    if expected_recipe != sol.recipe_effect:
        errors.append(
            f"recipe_effect mismatch: expected {expected_recipe}, got {sol.recipe_effect}"
        )

    expected_nature = tuple(apply_nature_effect(sol.nature))
    if expected_nature != sol.nature_effect:
        errors.append(
            f"nature_effect mismatch: expected {expected_nature}, got {sol.nature_effect}"
        )

    # Check the final modifiers meet the star thresholds
    mins = tuple(star_to_min_modifier(s) for s in stars)
    final_mods = tuple(
        r + n + d
        for r, n, d in zip(sol.recipe_effect, sol.nature_effect, sol.required_daily)
    )
    for i, (fm, mn) in enumerate(zip(final_mods, mins)):
        if fm < mn:
            errors.append(
                f"final modifier under target at idx={i} ({STAT_FLAVOR[i]}): "
                f"{fm} < {mn} (star={stars[i]})"
            )

    return errors


# Test data generators
def generate_exhaustive(values: Iterable[int]) -> list[intup]:
    """Generate all 5-tuple combinations from given values."""
    vals = list(values)
    result = []
    for a in vals:
        for b in vals:
            for c in vals:
                for d in vals:
                    for e in vals:
                        result.append((a, b, c, d, e))
    return result


STAR_WILDCARD_DOMAIN = (0, -1, -2, -3, -4)


def _all_unique_permutations(t: tuple[int, ...]) -> set[intup]:
    """Get all unique permutations of a tuple."""
    return set(permutations(t, 5))


def generate_required_permutation_suite() -> list[intup]:
    """Generate the required test suite.

    For each template, expand wildcards over STAR_WILDCARD_DOMAIN and
    include all unique permutations of each resulting 5-tuple.
    """
    cases: set[intup] = set()
    D = STAR_WILDCARD_DOMAIN

    patterns: list[tuple[tuple[int, ...], int]] = [
        ((4, 3, -4), 2),
        ((4, 3, -3, -1), 1),
        ((4, 2, -2, -1), 1),
        ((4, 2, -3), 2),
        ((4, 1, -2), 2),
        ((4, 1, -1, -1), 1),
        ((3, 3, 2, -4), 1),
        ((3, 3, 2, -3, -1), 0),
        ((3, 2, 2, -2, -1), 0),
        ((3, 2, 2, -3), 1),
        ((3, 2, 1, -2), 1),
        ((3, 2, 1, -1, -1), 0),
        ((2, 2, 2, -1, -1), 0),
        ((2, 2, 1, -1), 1),
        ((2, 1), 3),
        ((3, 0), 3),
    ]

    for base, k in patterns:
        for extras in product(D, repeat=k):
            cases |= _all_unique_permutations(base + extras)

    return sorted(cases)

def generate_edge_cases() -> list[intup]:
    edge_case = ((3, 1, 1, -1), 1)
    cases: set[intup] = set()
    D = STAR_WILDCARD_DOMAIN
    base, k = edge_case
    for extras in product(D, repeat=k):
        cases |= _all_unique_permutations(base + extras)
    
    return sorted(cases)

# Pytest test classes
class TestSolutionValidation:
    """Tests for solution validation across various star configurations."""

    def test_small_range_exhaustive(self):
        """Test all combinations of stars in range [-1, 2]."""
        for mode in ["min", "max"]:
            for stars in generate_exhaustive(range(-1, 3)):
                results = find_all_solutions(stars, mode=mode)
                
                for sol in results:
                    errors = validate_solution(stars, sol)
                    assert not errors, f"Validation failed for {stars} (mode={mode}): {errors}"

    def test_required_permutation_suite(self):
        """Test required permutation suite for edge cases."""
        for mode in ["min", "max"]:
            for stars in generate_required_permutation_suite():
                results = find_all_solutions(stars, mode=mode)
                
                assert len(results) > 0, f"No solutions found for {stars} (mode={mode})"
                for sol in results:
                    errors = validate_solution(stars, sol)
                    assert not errors, f"Validation failed for {stars} (mode={mode}): {errors}"

    def test_special_edge_cases(self):
        """Test required permutation suite for special edge case."""
        count = 0
        for mode in ["min", "max"]:
            for stars in generate_edge_cases():
                results = find_all_solutions(stars, mode=mode)
                
                if mode == "max":
                    assert len(results) > 0, f"No solutions found for {stars} (mode={mode})"
                elif mode == "min" and len(results) > 0:
                    count += 1
                    
                for sol in results:
                    errors = validate_solution(stars, sol)
                    assert not errors, f"Validation failed for {stars} (mode={mode}): {errors}"
                
        assert count > 0, f"Expected 30 solutions in min mode, got {count}"

    def test_all_zeros(self):
        """Test the trivial case of all zero stars."""
        stars = (0, 0, 0, 0, 0)
        
        for mode in ["min", "max"]:
            results = find_all_solutions(stars, mode=mode)
            assert len(results) > 0, f"Expected solutions for all zeros (mode={mode})"
            
            for sol in results:
                errors = validate_solution(stars, sol)
                assert not errors, f"Validation failed: {errors}"

    def test_single_high_star(self):
        """Test cases with a single high star requirement."""
        test_cases = [
            (4, -1, -1, -3, -1),
            (-1, 4, -1, -3, -1),
            (-1, -1, 4, -3, -1),
            (-1, -1, -3, 4, -1),
            (-1, -1, -3, -1, 4),
        ]
        
        for stars in test_cases:
            for mode in ["min", "max"]:
                results = find_all_solutions(stars, mode=mode)
                
                assert len(results) > 0, f"Expected solutions for {stars} (mode={mode})"
                for sol in results:
                    errors = validate_solution(stars, sol)
                    assert not errors, f"Validation failed for {stars} (mode={mode}): {errors}"


    def test_mixed_positive_negative(self):
        """Test mixed positive and negative star requirements."""
        test_cases = [
            (3, 2, 0, -1, -2),
            (2, 1, 0, -1, -2),
            (4, 1, -1, -2, -3),
            (3, 3, -2, -2, -2),
        ]
        
        for stars in test_cases:
            for mode in ["min", "max"]:
                results = find_all_solutions(stars, mode=mode)
                
                assert len(results) > 0, f"Expected solutions for {stars} (mode={mode})"
                for sol in results:
                    errors = validate_solution(stars, sol)
                    assert not errors, f"Validation failed for {stars} (mode={mode}): {errors}"

    def test_all_negative(self):
        """Test all negative star requirements."""
        test_cases = [
            (-1, -1, -1, -1, -1),
            (-2, -2, -2, -2, -2),
            (-3, -3, -3, -3, -3),
            (-4, -4, -4, -4, -4),
        ]
        
        for stars in test_cases:
            for mode in ["min", "max"]:
                results = find_all_solutions(stars, mode=mode)
                assert len(results) > 0, f"Expected solutions for {stars} (mode={mode})"
                
                for sol in results:
                    errors = validate_solution(stars, sol)
                    assert not errors, f"Validation failed for {stars} (mode={mode}): {errors}"


class TestConstraintSatisfaction:
    """Tests specifically for constraint satisfaction in solutions."""

    def test_flavor_caps_always_respected(self):
        """Verify flavor caps are never violated."""
        test_cases = generate_exhaustive(range(-1, 3))
        
        for stars in test_cases[:100]:  # Sample for performance
            for mode in ["min", "max"]:
                results = find_all_solutions(stars, mode=mode)
                
                for sol in results:
                    assert all(0 <= f <= 63 for f in sol.flavors), \
                        f"Flavor cap violated for {stars}: {sol.flavors}"
                    assert sum(sol.flavors) <= 100, \
                        f"Total flavor cap violated for {stars}: sum={sum(sol.flavors)}"

    def test_daily_modifiers_always_valid(self):
        """Verify daily modifiers are always odd and in range."""
        test_cases = generate_exhaustive(range(-1, 3))
        
        for stars in test_cases[:100]:  # Sample for performance
            for mode in ["min", "max"]:
                results = find_all_solutions(stars, mode=mode)
                
                for sol in results:
                    for daily in sol.required_daily:
                        assert daily % 2 != 0, \
                            f"Daily modifier not odd for {stars}: {daily}"
                        assert -9 <= daily <= 9, \
                            f"Daily modifier out of range for {stars}: {daily}"

    def test_final_modifiers_meet_thresholds(self):
        """Verify final modifiers always meet star thresholds."""
        test_cases = [
            (2, 1, 0, 0, 0),
            (3, 2, 1, 0, -4),
            (1, 1, 1, -1, -1),
            (4, 2, -1, -2, -2),
        ]
        
        for stars in test_cases:
            for mode in ["min", "max"]:
                results = find_all_solutions(stars, mode=mode)
                
                assert len(results) > 0, f"No solutions found for {stars} (mode={mode})"
                for sol in results:
                    mins = [star_to_min_modifier(s) for s in stars]
                    final_mods = [
                        r + n + d
                        for r, n, d in zip(
                            sol.recipe_effect,
                            sol.nature_effect,
                            sol.required_daily
                        )
                    ]
                    
                    for i, (fm, mn) in enumerate(zip(final_mods, mins)):
                        assert fm >= mn, \
                            f"Final modifier below threshold for {stars} at {STAT_FLAVOR[i]}: " \
                            f"{fm} < {mn}"


class TestModeComparison:
    """Tests comparing min vs max mode behavior."""

    def test_min_mode_produces_valid_solutions(self):
        """Test that min mode produces valid solutions."""
        test_cases = [
            (2, 1, 0, 0, 0),
            (1, 1, 1, 0, 0),
            (3, 2, -2, 0, 0),
        ]
        
        for stars in test_cases:
            results = find_all_solutions(stars, mode="min")
            
            assert len(results) > 0, f"Expected solutions for {stars} (mode=min)"
            for sol in results:
                errors = validate_solution(stars, sol)
                assert not errors, f"Min mode validation failed for {stars}: {errors}"

    def test_max_mode_produces_valid_solutions(self):
        """Test that max mode produces valid solutions."""
        test_cases = [
            (2, 1, 0, 0, 0),
            (1, 1, 1, 0, 0),
            (3, 2, -1, 0, 0),
        ]
        
        for stars in test_cases:
            results = find_all_solutions(stars, mode="max")
            
            assert len(results) > 0, f"Expected solutions for {stars} (mode=max)"
            for sol in results:
                errors = validate_solution(stars, sol)
                assert not errors, f"Max mode validation failed for {stars}: {errors}"

    def test_both_modes_satisfy_constraints(self):
        """Test that both modes satisfy all constraints for same input."""
        test_cases = [
            (2, 1, 0, 0, 0),
            (3, 2, 1, 0, -4),
            (1, 1, 1, -1, 0),
        ]
        
        for stars in test_cases:
            for mode in ["min", "max"]:
                results = find_all_solutions(stars, mode=mode)
                assert len(results) > 0, f"Expected solutions for {stars} (mode={mode})"
                for sol in results:
                    errors = validate_solution(stars, sol)
                    assert not errors, \
                        f"Mode {mode} validation failed for {stars}: {errors}"
