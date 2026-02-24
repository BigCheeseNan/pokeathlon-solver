from __future__ import annotations
import argparse
from solver_core.constants import (
    NATURE_TO_INDEX,
    STAT_FLAVOR,
    intup,
    SeedSearchResult,
    Result,
)
from solver_core.poke_finder import find_lowest_total_pokemon
from solver_core.main import (
    find_all_solutions,
    pokemon_to_star_diffs,
    reorder_speed_to_stat_flavor,
    reorder_stat_flavor_to_speed,
)
from solver_core.recipe import astar_minimal_recipe as astar_py_backup, reduce_recipe


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Link star-bonus targets -> best (nature, flavors) -> required daily modifiers, "
            "then compute minimal ingredient recipes and working Seed/PID."
        )
    )

    parser.add_argument(
        "stars",
        nargs="+",
        type=str,
        help=(
            "Stars input for all modes (5 values). Accepts space-separated or comma-separated values. "
            "In diffs mode: each in [-4..4]. In pokemon/candidates mode: each in [1..5]. "
            "Default order is power order."
        ),
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["diffs", "pokemon", "candidates"],
        default="diffs",
        help=(
            "Diffs mode (default): solve for (nature, flavor) pairs. "
            "Pokemon mode: solve for candidate Pokemon meeting minimum stats. "
            "Candidates mode: only output candidate Pokemon without solving."
        ),
    )

    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument(
        "--min",
        dest="target",
        action="store_const",
        const="min",
        help="Flavor search mode: minimal ingredients (default).",
    )
    target_group.add_argument(
        "--max",
        dest="target",
        action="store_const",
        const="max",
        help="Flavor search mode: easiest daily requirements.",
    )
    parser.set_defaults(target="min")

    order_group = parser.add_mutually_exclusive_group()
    order_group.add_argument(
        "--power-order",
        dest="star_order",
        action="store_const",
        const="power",
        help="Power order: power stamina skill jump speed (default).",
    )
    order_group.add_argument(
        "--speed-order",
        dest="star_order",
        action="store_const",
        const="speed",
        help="Speed order: speed power skill stamina jump.",
    )
    parser.set_defaults(star_order="power")

    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="In pokemon or candidates mode: number of candidate Pokemon to consider (default: 10).",
    )

    parser.add_argument(
        "--full",
        default=False,
        const=True,
        action="store_const",
        help="In Pokemon mode: show all solutions instead of just the best one",
    )

    args = parser.parse_args()

    # Build a list of "cases" to solve.
    cases: list[tuple[str, intup]] = []

    raw_tokens: list[str] = []
    for item in args.stars:
        raw_tokens.extend(token.strip() for token in item.split(",") if token.strip())

    if len(raw_tokens) != 5:
        raise SystemExit(
            "Expected 5 star values (space-separated or comma-separated). "
            "Examples: '2 1 0 -2 3' or '2,1,0,-2,3'."
        )

    try:
        stars = tuple(int(t) for t in raw_tokens)
    except ValueError as exc:
        raise SystemExit("Stars values must be integers.") from exc

    if args.mode in ("pokemon", "candidates"):
        for s in stars:
            if s < 1 or s > 5:
                raise SystemExit(
                    "stars values must be in [1..5] for pokemon/candidates mode"
                )

        desired_stars_speed_order = (
            reorder_stat_flavor_to_speed(stars) if args.star_order == "power" else stars
        )

        candidates = find_lowest_total_pokemon(
            desired_stars_speed_order,
            top_n=args.top_n,
        )
        if not candidates:
            print(
                "No Pokemon can meet those minimum stats under the current constraints."
            )
            return 2

        stats_string = (
            "(power,stamina,skill,jump,speed)"
            if args.star_order == "power"
            else "(speed,power,skill,stamina,jump)"
        )

        print("=== Pokemon search ===")
        print(
            f"Desired minimum stats {stats_string}:",
            stars,
        )
        print(f"Candidates considered: {len(candidates)} (lowest total first)")
        for i, p in enumerate(candidates, start=1):
            base = (
                (p.speed, p.power, p.skill, p.stamina, p.jump)
                if args.star_order == "speed"
                else (p.power, p.stamina, p.skill, p.jump, p.speed)
            )
            max_stats = (
                (p.speedMax, p.powerMax, p.skillMax, p.staminaMax, p.jumpMax)
                if args.star_order == "speed"
                else (p.powerMax, p.staminaMax, p.skillMax, p.jumpMax, p.speedMax)
            )
            print(
                f"[{i}] {p.name} (id={p.id}) total={p.total} base={base} max={max_stats}"
            )
        print()

        if args.mode == "candidates":
            return 0

        for p in candidates:
            diffs = pokemon_to_star_diffs(desired_stars_speed_order, p)
            cases.append((f"Pokemon={p.name} (id={p.id}) total={p.total}", diffs))
    else:
        for s in stars:
            if s < -4 or s > 4:
                raise SystemExit("stars values must be in [-4..4] for diffs mode")

        desired_star_diffs = (
            reorder_speed_to_stat_flavor(stars) if args.star_order == "speed" else stars
        )
        cases.append(("", desired_star_diffs))

    mode: str = args.target or "min"

    # Load C solver once (if available) to speed up repeated recipe solves.
    print_header_once = True

    def compute_recipe(flavors: intup) -> tuple[list[str] | None, float | None, str]:
        try:
            from solver_core.bindings import astar_minimal_recipe

            recipe, elapsed, err = astar_minimal_recipe(
                flavors, quiet=True, prune_relevant=True
            )
            if recipe is not None:
                return recipe, elapsed, "c"
        except Exception:
            print("C solver failed; falling back to Python solver.")
            pass
        recipe = astar_py_backup(flavors)
        return recipe, None, "python"

    exit_code = 0
    for case_label, desired_star_diffs in cases:
        solutions = find_all_solutions(desired_star_diffs, mode)
        if not solutions:
            if case_label:
                print(f"=== {case_label} ===")
            print(
                "No feasible (nature, flavor) solution found under the current search space."
            )
            print()
            exit_code = max(exit_code, 2)
            continue

        if case_label:
            print(f"=== {case_label} ===")

        if print_header_once:
            print("=== Inputs ===")
            print_header_once = False

        print(
            "Desired star diffs (power,stamina,skill,jump,speed):", desired_star_diffs
        )
        print()

        ranked: list[Result] = []
        skipped_recipes = 0
        for sol in solutions:
            recipe, elapsed, source = compute_recipe(sol.flavors)
            if recipe is None:
                skipped_recipes += 1
                continue
            grouped = reduce_recipe(recipe, sol.flavors)
            seed_result: SeedSearchResult | None = None
            try:
                from solver_core.bindings import find_best_seed_for_criteria

                seed_result = find_best_seed_for_criteria(
                    sol.required_daily,
                    allowed_mod=NATURE_TO_INDEX[sol.nature],
                    quiet=True,
                )
            except Exception:
                # Optional feature: don't fail the whole script if the DLL isn't present.
                seed_result = None
            final_mods = [
                r + n + d
                for r, n, d in zip(
                    sol.recipe_effect, sol.nature_effect, sol.required_daily
                )
            ]
            ranked.append(
                Result(
                    sol=sol,
                    recipe=recipe,
                    grouped=grouped,
                    elapsed=elapsed,
                    source=source,
                    ingredients=len(recipe),
                    daily_sum=sum(sol.required_daily),
                    final_mods=final_mods,
                    seed_result=seed_result,
                )
            )

        if not ranked:
            print(
                "Found feasible (nature, flavor) pairs, but no ingredient recipe was produced."
            )
            print()
            exit_code = max(exit_code, 5)
            continue

        if mode == "min":
            ranked.sort(
                key=lambda r: (
                    r.ingredients,
                    -r.seed_result.streak if r.seed_result is not None else 10**9,
                    NATURE_TO_INDEX[r.sol.nature],
                )
            )
        else:
            ranked.sort(
                key=lambda r: (
                    r.seed_result.num_offsets if r.seed_result is not None else 10**9,
                    r.seed_result.streak if r.seed_result is not None else -1,
                    -r.ingredients,
                    -NATURE_TO_INDEX[r.sol.nature],
                ),
                reverse=True,
            )

        print(
            f"=== Working solutions (ranked by ingredient count, then lower required daily) ==="
        )
        print(
            f"Total feasible nature/flavor pairs: {len(solutions)} | With recipes: {len(ranked)} | Recipe failures: {skipped_recipes}"
        )

        for idx, entry in enumerate(ranked, start=1):
            sol = entry.sol
            nat_name, nat_plus, nat_minus, nat_neutral = sol.nature
            nat_idx = NATURE_TO_INDEX[sol.nature]
            elapsed = entry.elapsed
            solver_tag = f"{entry.source}" + (
                f" {elapsed:.3f}s" if elapsed is not None else ""
            )
            print(
                f"[#{idx}] ingredients={entry.ingredients} daily_sum={entry.daily_sum} | "
                f"nature ({nat_idx}) {nat_name} (+{STAT_FLAVOR[nat_plus]}, -{STAT_FLAVOR[nat_minus]}, neutral={nat_neutral}) | solver={solver_tag}"
            )
            print("  required daily:", sol.required_daily)
            print("  flavors (spicy,sour,dry,bitter,sweet):", sol.flavors)
            print("  mildness:", sol.mildness)
            print("  recipe contribution:", sol.recipe_effect)
            print("  nature contribution:", sol.nature_effect)
            print("  final modifiers:", entry.final_mods)
            print(
                "  ingredients:",
                ", ".join(f"{ing} x{cnt}" for ing, cnt in entry.grouped),
            )
            if entry.seed_result is not None:
                sr = entry.seed_result
                print(
                    f"  PID: {hex(sr.pid)} | seed: {hex(sr.seed)} | "
                    f"days: {list(sr.x_values) if len(sr.x_values) < 31 else 'All days'} (streak={sr.streak}, count={sr.count})"
                )
                print(
                    f"  natural catch probability: {sr.natural_catch_probability:.6%} "
                    f"(num_offsets={sr.num_offsets})"
                )
            else:
                print("  PID/seed: (seed DLL not available)")
            print()
            if not args.full and not args.mode == "diffs":
                break

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
