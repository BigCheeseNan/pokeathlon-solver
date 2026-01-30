import { useCallback, useState } from "react";
import { postPokemonCandidates } from "../api";
import type {
    PokemonCandidatesRequest,
    PokemonCandidatesResponse,
} from "../types";
import { toErrorMessage } from "../utils/errors";

export type PokemonCandidatesParams = {
    stars: PokemonCandidatesRequest["stars"];
    pokemonTopN: PokemonCandidatesRequest["pokemon_top_n"];
    searchMode: PokemonCandidatesRequest["search_mode"];
};

export function usePokemonCandidates() {
    const [candidates, setCandidates] = useState<PokemonCandidatesResponse | null>(
        null
    );
    const [isSearching, setIsSearching] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const search = useCallback(async (params: PokemonCandidatesParams) => {
        setError(null);
        setCandidates(null);
        setIsSearching(true);
        try {
            const body = {
                stars: params.stars,
                pokemon_top_n: params.pokemonTopN,
                search_mode: params.searchMode,
            };
            setCandidates(await postPokemonCandidates(body));
        } catch (err) {
            setError(toErrorMessage(err));
        } finally {
            setIsSearching(false);
        }
    }, []);

    const clearError = useCallback(() => setError(null), []);
    const reset = useCallback(() => setCandidates(null), []);

    return { candidates, isSearching, error, search, clearError, reset };
}
