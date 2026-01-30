import type {
    DiffsResponse,
    PokemonCandidatesRequest,
    PokemonCandidatesResponse,
    SolveRequest,
} from "./types";

export async function postSolve(body: SolveRequest): Promise<DiffsResponse> {
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
    body: PokemonCandidatesRequest
): Promise<PokemonCandidatesResponse> {
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
