import { useCallback, useState } from "react";
import { postSolve } from "../api";
import type { CaseResult, PokemonCandidate, SolveRequest } from "../types";
import { toErrorMessage } from "../utils/errors";

export type PokemonSolverParams = {
    candidate: PokemonCandidate;
    computeSeed: SolveRequest["compute_seed"];
    searchMode: SolveRequest["search_mode"];
    allowedXValues: number[];
};

export function usePokemonSolver() {
    const [result, setResult] = useState<CaseResult | null>(null);
    const [isSolving, setIsSolving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const solve = useCallback(async (params: PokemonSolverParams) => {
        setError(null);
        setResult(null);
        setIsSolving(true);
        try {
            const body: SolveRequest = {
                mode: "diffs",
                star_diffs: params.candidate.computed_diffs,
                compute_seed: params.computeSeed,
                search_mode: params.searchMode,
                allowed_x_values: params.allowedXValues.length > 0 ? params.allowedXValues : null,
            };
            const res = await postSolve(body);
            const label = `${params.candidate.name} (bonus points: ${25 - params.candidate.total})`;
            setResult({ ...res.case, label });
        } catch (err) {
            setError(toErrorMessage(err));
        } finally {
            setIsSolving(false);
        }
    }, []);

    const clearError = useCallback(() => setError(null), []);
    const reset = useCallback(() => setResult(null), []);

    return { result, isSolving, error, solve, clearError, reset };
}
