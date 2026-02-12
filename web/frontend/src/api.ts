import type {
    DiffsResponse,
    PokemonCandidatesRequest,
    PokemonCandidatesResponse,
    SolveRequest,
} from "./types";
import { localPostPokemonCandidates, localPostSolve } from "./localSolver";

const solverMode = (import.meta.env.VITE_SOLVER_MODE ?? "remote") as "remote" | "local" | "auto";

export async function postSolve(body: SolveRequest): Promise<DiffsResponse> {
    if (solverMode !== "remote") {
        try {
            return await localPostSolve(body);
        } catch (err) {
            if (solverMode === "local") throw err;
        }
    }

    const resp = await fetch("/api/solve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(`${resp.status} ${resp.statusText}: ${txt}`);
    }
    return (await resp.json()) as DiffsResponse;
}

export async function postPokemonCandidates(
    body: PokemonCandidatesRequest,
): Promise<PokemonCandidatesResponse> {
    if (solverMode !== "remote") {
        try {
            return await localPostPokemonCandidates(body);
        } catch (err) {
            if (solverMode === "local") throw err;
        }
    }

    const resp = await fetch("/api/pokemon/candidates", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(`${resp.status} ${resp.statusText}: ${txt}`);
    }
    return (await resp.json()) as PokemonCandidatesResponse;
}
