export type Mode = "diffs" | "pokemon";

export type SeedResult = {
    pid: number;
    seed: number;
    days: number[];
    streak: number;
    count: number;
    num_offsets: number;
    natural_catch_probability: number;
};

export type Solution = {
    ingredients: number;
    daily_sum: number;
    solver_source: string;
    nature: {
        name: string;
        plus: string;
        minus: string;
        delta: number;
        index: number;
    };
    required_daily: number[];
    flavors: number[];
    mildness: number;
    grouped_ingredients: Array<{ ingredient: FlavorKey; count: number }>;
    seed_result: SeedResult | null;
};

export type CaseResult = {
    label: string;
    desired_star_diffs: number[];
    solutions_total: number;
    solutions_with_recipes: number;
    recipe_failures: number;
    invalid_seeds: number;
    results: Solution[];
    error: string | null;
};

export type DiffsResponse = { mode: Mode; case: CaseResult };

// NOTE: Only "diffs" is used for solve calls. The previous "pokemon" solve
// mode was removed when the UX changed to select a single candidate and solve
// per-choice instead of solving all candidates at once.
export type SolveRequest = {
    mode: Mode;
    star_diffs: number[];
    compute_seed: boolean;
    search_mode: "min" | "max";
    allowed_x_values: number[] | null;
};

export type PokemonCandidate = {
    id: number;
    dex_id: string;
    name: string;
    total: number;
    base: number[];
    min: number[];
    max: number[];
    computed_diffs: number[];
};

export type PokemonCandidatesResponse = {
    mode: "pokemon_candidates";
    desired_stars: number[];
    candidates: PokemonCandidate[];
};

export type PokemonCandidatesRequest = {
    stars: number[];
    pokemon_top_n: number;
    search_mode: "min" | "max";
};

export type StatKey = "speed" | "power" | "skill" | "stamina" | "jump";

export type FlavorKey = "spicy" | "dry" | "sweet" | "bitter" | "sour" | "strong" | "mild";
