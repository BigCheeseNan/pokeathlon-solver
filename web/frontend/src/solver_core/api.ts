import type { IntTuple, Nature, Result, SeedSearchResult, FlavorKey } from "./constants";
import {
    INGREDIENTS,
    NATURES,
    STAT_FLAVOR,
    naturalCatchProbability,
    seedXValues,
} from "./constants";
import { findLowestTotalPokemon } from "./poke_finder";
import { findAllSolutions } from "./main";
import { reduceRecipe } from "./recipe";
import { natureKey, NATURE_TO_INDEX, pokemonToStarDiffs } from "./utils";

export type SolveOptions = {
    compute_seed?: boolean;
    top_n_solutions?: number | null;
    pokemon_top_n?: number;
    search_mode?: "min" | "max";
    allowed_x_values?: number[] | null;
};

export type SeedResultDict = {
    pid: number;
    seed: number;
    days: number[];
    streak: number;
    count: number;
    num_offsets: number;
    natural_catch_probability: number;
};

export type SolutionDict = {
    ingredients: number;
    daily_sum: number;
    solver_source: string;
    nature: {
        name: string;
        plus: string;
        minus: string;
        plus_idx: number;
        minus_idx: number;
        neutral: boolean;
        delta: number;
        index: number;
    };
    required_daily: number[];
    flavors: number[];
    mildness: number;
    recipe_effect: number[];
    nature_effect: number[];
    final_mods: number[];
    grouped_ingredients: Array<{ ingredient: FlavorKey; count: number }>;
    seed_result: SeedResultDict | null;
};

export type CaseResultDict = {
    label: string;
    desired_star_diffs: number[];
    solutions_total: number;
    solutions_with_recipes: number;
    recipe_failures: number;
    invalid_seeds: number;
    results: SolutionDict[];
    error: string | null;
};

export type PokemonCandidateDict = {
    id: number;
    dex_id: string;
    name: string;
    total: number;
    base: number[];
    min: number[];
    max: number[];
    computed_diffs: number[];
};

export type PokemonCandidatesResponseDict = {
    mode: "pokemon_candidates";
    desired_stars: number[];
    candidates: PokemonCandidateDict[];
};

export type RecipeCompute = (
    flavors: IntTuple,
    opts?: { quiet?: boolean; prune_relevant?: boolean },
) => Promise<{ recipe: string[] | null; source: string }>;

export type SeedCompute = (
    requiredDaily: IntTuple,
    allowedMod: number,
    allowedXValues?: number[] | null,
    opts?: { quiet?: boolean },
) => Promise<SeedSearchResult | null>;

export type SolverDeps = {
    recipe?: RecipeCompute;
    seed?: SeedCompute;
};

function groupedToJson(grouped: Array<[string, number]>) {
    return grouped.map(([ingredient, count]) => ({
        ingredient: ingredient as FlavorKey,
        count,
    }));
}

function seedToJson(sr: SeedSearchResult): SeedResultDict {
    return {
        pid: sr.pid,
        seed: sr.seed,
        days: seedXValues(sr.x_mask),
        streak: sr.streak,
        count: sr.count,
        num_offsets: sr.num_offsets,
        natural_catch_probability: naturalCatchProbability(sr.num_offsets),
    };
}

function natureToJson(nat: Nature) {
    const [name, plusIdx, minusIdx, neutralFlag] = nat;
    const key = natureKey(nat);
    const index = NATURE_TO_INDEX.get(key) ?? 0;
    return {
        name,
        plus: STAT_FLAVOR[plusIdx],
        minus: STAT_FLAVOR[minusIdx],
        plus_idx: plusIdx,
        minus_idx: minusIdx,
        neutral: neutralFlag,
        delta: neutralFlag ? 10 : 35,
        index,
    };
}

export function listPokemonCandidates(
    desiredStarsSpeedOrder: IntTuple,
    opts?: { top_n?: number },
): PokemonCandidatesResponseDict {
    for (const s of desiredStarsSpeedOrder) {
        if (s < 1 || s > 5) {
            throw new Error("desired_stars_speed_order values must be in [1..5]");
        }
    }

    const candidates = findLowestTotalPokemon(desiredStarsSpeedOrder, undefined, opts?.top_n ?? 10);

    return {
        mode: "pokemon_candidates",
        desired_stars: [...desiredStarsSpeedOrder],
        candidates: candidates.map((p) => ({
            id: p.id,
            dex_id: String(p.dex_id),
            name: p.name,
            total: p.total,
            base: [p.speed, p.power, p.skill, p.stamina, p.jump],
            min: [p.speedMin, p.powerMin, p.skillMin, p.staminaMin, p.jumpMin],
            max: [p.speedMax, p.powerMax, p.skillMax, p.staminaMax, p.jumpMax],
            computed_diffs: [...pokemonToStarDiffs(desiredStarsSpeedOrder, p)],
        })),
    };
}

export async function solveFromStarDiffs(
    desiredStarDiffs: IntTuple,
    options?: SolveOptions,
    deps?: SolverDeps,
): Promise<CaseResultDict> {
    let recipeCount = 0;
    let seedCount = 0;
    const opts: Required<SolveOptions> = {
        compute_seed: options?.compute_seed ?? true,
        top_n_solutions: options?.top_n_solutions ?? null,
        pokemon_top_n: options?.pokemon_top_n ?? 10,
        search_mode: options?.search_mode ?? "min",
        allowed_x_values: options?.allowed_x_values ?? null,
    };

    const solutions = findAllSolutions(desiredStarDiffs, opts.search_mode);
    if (solutions.length === 0) {
        return {
            label: "",
            desired_star_diffs: [...desiredStarDiffs],
            solutions_total: 0,
            solutions_with_recipes: 0,
            recipe_failures: 0,
            invalid_seeds: 0,
            results: [],
            error: "No feasible (nature, flavor) solution found under the current search space.",
        };
    }

    const ranked: Result[] = [];
    let skippedRecipes = 0;
    let invalidSeeds = 0;

    for (const sol of solutions) {
        if (!deps?.recipe) {
            console.error("No recipe solver configured");
            throw new Error("Recipe solver not configured. Provide WASM recipe bindings.");
        }
        const recipeRes = await deps.recipe(sol.flavors, {
            quiet: true,
            prune_relevant: true,
        });
        recipeCount += 1;
        if (!recipeRes.recipe) {
            console.error("No recipe produced");
            skippedRecipes += 1;
            continue;
        }

        const grouped = reduceRecipe(recipeRes.recipe, sol.flavors);
        let seedResult: SeedSearchResult | null = null;
        if (opts.compute_seed) {
            if (!deps?.seed) {
                throw new Error("Seed solver not configured. Provide WASM seed bindings.");
            }
            const key = natureKey(sol.nature);
            const natIndex = NATURE_TO_INDEX.get(key) ?? 0;
            seedResult = await deps.seed(sol.required_daily, natIndex, opts.allowed_x_values, {
                quiet: true,
            });
            seedCount += 1;
            if (!seedResult || seedResult.count === 0) {
                console.error("No valid seed found");
                console.error("Solution:", sol);
                invalidSeeds += 1;
                continue;
            }
        }

        const finalMods = sol.recipe_effect.map(
            (r, i) => r + sol.nature_effect[i] + sol.required_daily[i],
        );

        ranked.push({
            sol,
            recipe: recipeRes.recipe,
            grouped,
            source: recipeRes.source,
            ingredients: recipeRes.recipe.length,
            daily_sum: sol.required_daily.reduce((a, b) => a + b, 0),
            final_mods: finalMods,
            seed_result: seedResult,
        });
    }

    if (ranked.length === 0) {
        return {
            label: "",
            desired_star_diffs: [...desiredStarDiffs],
            solutions_total: solutions.length,
            solutions_with_recipes: 0,
            recipe_failures: skippedRecipes,
            invalid_seeds: invalidSeeds,
            results: [],
            error: "Found feasible (nature, flavor) pairs, but no ingredient recipe was produced.",
        };
    }

    if (opts.search_mode === "min") {
        ranked.sort((a, b) => {
            const aNat = NATURE_TO_INDEX.get(natureKey(a.sol.nature)) ?? 0;
            const bNat = NATURE_TO_INDEX.get(natureKey(b.sol.nature)) ?? 0;
            return (
                a.ingredients - b.ingredients ||
                a.sol.mildness - b.sol.mildness ||
                (b.seed_result?.streak ?? 10 ** 9) - (a.seed_result?.streak ?? 10 ** 9) ||
                (b.seed_result?.count ?? 10 ** 9) - (a.seed_result?.count ?? 10 ** 9) ||
                aNat - bNat
            );
        });
    } else {
        ranked.sort((a, b) => {
            const aNat = NATURE_TO_INDEX.get(natureKey(a.sol.nature)) ?? 0;
            const bNat = NATURE_TO_INDEX.get(natureKey(b.sol.nature)) ?? 0;
            return (
                (b.seed_result?.num_offsets ?? 10 ** 9) - (a.seed_result?.num_offsets ?? 10 ** 9) ||
                a.ingredients - b.ingredients ||
                a.sol.mildness - b.sol.mildness ||
                (b.seed_result?.streak ?? 10 ** 9) - (a.seed_result?.streak ?? 10 ** 9) ||
                (b.seed_result?.count ?? 10 ** 9) - (a.seed_result?.count ?? 10 ** 9) ||
                bNat - aNat
            );
        });
    }

    const results: SolutionDict[] = ranked.map((entry) => ({
        ingredients: entry.ingredients,
        daily_sum: entry.daily_sum,
        solver_source: entry.source,
        nature: natureToJson(entry.sol.nature),
        required_daily: [...entry.sol.required_daily],
        flavors: [...entry.sol.flavors],
        mildness: entry.sol.mildness,
        recipe_effect: [...entry.sol.recipe_effect],
        nature_effect: [...entry.sol.nature_effect],
        final_mods: [...entry.final_mods],
        grouped_ingredients: groupedToJson(entry.grouped),
        seed_result: entry.seed_result ? seedToJson(entry.seed_result) : null,
    }));

    return {
        label: "",
        desired_star_diffs: [...desiredStarDiffs],
        solutions_total: solutions.length,
        solutions_with_recipes: solutions.length - skippedRecipes,
        recipe_failures: skippedRecipes,
        invalid_seeds: invalidSeeds,
        results,
        error: null,
    };
}

export async function solveFromPokemonStars(
    desiredStarsSpeedOrder: IntTuple,
    options?: SolveOptions,
    deps?: SolverDeps,
): Promise<{
    mode: "pokemon";
    desired_stars: number[];
    candidates: PokemonCandidateDict[];
    cases: CaseResultDict[];
}> {
    for (const s of desiredStarsSpeedOrder) {
        if (s < 1 || s > 5) {
            throw new Error("desired_stars_speed_order values must be in [1..5]");
        }
    }

    const candidates = findLowestTotalPokemon(
        desiredStarsSpeedOrder,
        undefined,
        options?.pokemon_top_n ?? 10,
    );

    const cases: CaseResultDict[] = [];
    for (const p of candidates) {
        const diffs = pokemonToStarDiffs(desiredStarsSpeedOrder, p);
        const caseRes = await solveFromStarDiffs(diffs, options, deps);
        caseRes.label = `Pokemon=${p.name} (id=${p.id}) total=${p.total}`;
        cases.push(caseRes);
    }

    return {
        mode: "pokemon",
        desired_stars: [...desiredStarsSpeedOrder],
        candidates: candidates.map((p) => ({
            id: p.id,
            dex_id: p.dex_id,
            name: p.name,
            total: p.total,
            base: [p.speed, p.power, p.skill, p.stamina, p.jump],
            min: [p.speedMin, p.powerMin, p.skillMin, p.staminaMin, p.jumpMin],
            max: [p.speedMax, p.powerMax, p.skillMax, p.staminaMax, p.jumpMax],
            computed_diffs: [...pokemonToStarDiffs(desiredStarsSpeedOrder, p)],
        })),
        cases,
    };
}

export const RecipeIngredientIndex: Record<string, number> = INGREDIENTS.reduce(
    (acc, ing, idx) => {
        acc[ing] = idx;
        return acc;
    },
    {} as Record<string, number>,
);

export const NaturesIndex: Nature[] = NATURES;
