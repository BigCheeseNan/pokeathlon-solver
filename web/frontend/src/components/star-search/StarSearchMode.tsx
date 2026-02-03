import { type FormEvent, useCallback, useMemo, useReducer, useState } from "react";
import type { PokemonCandidate } from "../../types";
import { usePokemonCandidates } from "../../hooks/usePokemonCandidates";
import { usePokemonSolver } from "../../hooks/usePokemonSolver";
import CandidateList from "./CandidateList";
import StarSearchForm, { type StarFormValues } from "./StarSearchForm";
import StarSearch from "./StarSearchResult";

const initialFormState: StarFormValues = {
    stars: [5, 5, 2, 4, 1],
    pokemonTopN: 5,
    computeSeed: true,
    searchMode: "min",
    allowedXValues: "",
    topNSolutions: 3,
    showAdvanced: false,
};

const formReducer = <K extends keyof StarFormValues>(
    state: StarFormValues,
    action: { key: K; value: StarFormValues[K] }
): StarFormValues => ({
    ...state,
    [action.key]: action.value,
});

function StarSearchMode() {
    const [formValues, dispatch] = useReducer(formReducer, initialFormState);
    const [selectedPokemon, setSelectedPokemon] = useState<PokemonCandidate | null>(null);
    const {
        candidates,
        isSearching,
        error: searchError,
        search,
        clearError: clearSearchError,
        reset: resetCandidates,
    } = usePokemonCandidates();
    const {
        result,
        isSolving,
        error: solveError,
        solve,
        clearError: clearSolveError,
        reset: resetResult,
    } = usePokemonSolver();

    const starLabels = useMemo(
        () => ["speed", "power", "skill", "stamina", "jump"],
        []
    );

    const allowedXValuesParsed = useMemo(
        () =>
            formValues.allowedXValues
                .split(",")
                .map((s) => parseInt(s.trim(), 10))
                .filter((n) => !isNaN(n) && n >= 1 && n <= 31),
        [formValues.allowedXValues]
    );

    const displayedCandidates = useMemo(
        () => candidates?.candidates ?? [],
        [candidates]
    );

    const error = searchError ?? solveError;

    const copy = useCallback(async (text: string) => {
        try {
            await navigator.clipboard.writeText(text);
        } catch {
            // ignore
        }
    }, []);

    const onSubmit = useCallback(async (e: FormEvent) => {
        e.preventDefault();
        clearSearchError();
        clearSolveError();
        resetCandidates();
        setSelectedPokemon(null);
        resetResult();
        await search({
            stars: formValues.stars,
            pokemonTopN: formValues.pokemonTopN,
            searchMode: formValues.searchMode,
        });
    }, [
        clearSearchError,
        clearSolveError,
        search,
        formValues.stars,
        formValues.pokemonTopN,
        formValues.searchMode,
        resetCandidates,
        resetResult,
    ]);

    const solvePokemon = useCallback(
        async (p: PokemonCandidate) => {
            clearSearchError();
            clearSolveError();
            setSelectedPokemon(p);
            resetResult();
            await solve({
                candidate: p,
                computeSeed: formValues.computeSeed,
                searchMode: formValues.searchMode,
                allowedXValues: allowedXValuesParsed,
            });
        },
        [
            allowedXValuesParsed,
            clearSearchError,
            clearSolveError,
            resetResult,
            formValues.computeSeed,
            formValues.searchMode,
            solve,
        ]
    );

    const onFormChange = useCallback(
        <K extends keyof StarFormValues>(
            key: K,
            value: StarFormValues[K]
        ) => {
            dispatch({ key, value });
        },
        []
    );

    return (
        <>
            <StarSearchForm
                starLabels={starLabels}
                values={formValues}
                onChange={onFormChange}
                isSearching={isSearching}
                error={error}
                onSubmit={onSubmit}
            />

            {candidates ? (
                <section className="results">
                    <h2>Candidate Pokemon</h2>
                    <CandidateList
                        candidates={displayedCandidates}
                        selectedPokemon={selectedPokemon}
                        onSelect={solvePokemon}
                    />

                    <StarSearch
                        result={result}
                        isSolving={isSolving}
                        selectedPokemon={selectedPokemon}
                        copy={copy}
                        showAdvanced={formValues.showAdvanced}
                        showSeed={formValues.computeSeed}
                        topNSolutions={formValues.topNSolutions}
                    />
                </section>
            ) : null}
        </>
    );
}

export default StarSearchMode;
