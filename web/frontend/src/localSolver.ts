import type {
    DiffsResponse,
    PokemonCandidatesRequest,
    PokemonCandidatesResponse,
    SolveRequest,
} from "./types";
import { listPokemonCandidates, solveFromStarDiffs, type SolverDeps } from "./solver_core";
import { createWasmSolverDeps } from "./solver_core";

let depsPromise: Promise<SolverDeps> | null = null;

async function getDeps(): Promise<SolverDeps> {
    if (!depsPromise) {
        depsPromise = createWasmSolverDeps();
    }
    return depsPromise;
}

export async function localPostSolve(body: SolveRequest): Promise<DiffsResponse> {
    if (body.mode !== "diffs") {
        throw new Error("Only mode=diffs is supported in local solver");
    }
    if (!body.star_diffs || body.star_diffs.length !== 5) {
        throw new Error("star_diffs must be a list of 5 ints");
    }

    const deps = await getDeps();
    // Yield once so the UI can render the loading state before heavy work.
    await new Promise<void>((resolve) => setTimeout(resolve, 0));
    const caseRes = await solveFromStarDiffs(
        body.star_diffs,
        {
            compute_seed: body.compute_seed,
            search_mode: body.search_mode,
            allowed_x_values: body.allowed_x_values,
        },
        deps,
    );

    return { mode: "diffs", case: caseRes };
}

export async function localPostPokemonCandidates(
    body: PokemonCandidatesRequest,
): Promise<PokemonCandidatesResponse> {
    if (!body.stars || body.stars.length !== 5) {
        throw new Error("pokemon_stars must be a list of 5 ints");
    }
    return listPokemonCandidates(body.stars, { top_n: body.pokemon_top_n });
}
