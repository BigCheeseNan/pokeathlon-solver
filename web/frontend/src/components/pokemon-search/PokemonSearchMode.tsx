import { type FormEvent, useCallback, useMemo, useReducer, useState } from "react";
import type { CaseResult, SolveRequest, StatKey } from "../../types";
import { DIFFS_ORDER, STAT_ORDER } from "../../constants";
import { FULL_POKEMON, baseStars, clampInt, dex3, getTriplet } from "../../utils/pokemon";
import { postSolve } from "../../api";
import { toErrorMessage } from "../../utils/errors";
import PokemonPicker from "./PokemonPicker";
import StarEditor from "./StarEditor";
import SolverForm, { type SolverFormValues } from "./SolverForm";
import PokemonResult from "./PokemonResult";

const initialFormState: SolverFormValues = {
    computeSeed: true,
    searchMode: "min",
    allowedXValues: "",
    showAdvanced: false,
    topNSolutions: 3,
};

const formReducer = <K extends keyof SolverFormValues>(
    state: SolverFormValues,
    action: { key: K; value: SolverFormValues[K] },
): SolverFormValues => ({
    ...state,
    [action.key]: action.value,
});

function PokemonSearchMode() {
    const [pokemonInput, setPokemonInput] = useState<string>("");
    const [pokemonId, setPokemonId] = useState<number | null>(null);
    const [desired, setDesired] = useState<Record<StatKey, number>>({
        speed: 1,
        power: 1,
        skill: 1,
        stamina: 1,
        jump: 1,
    });
    const [formValues, dispatch] = useReducer(formReducer, initialFormState);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<CaseResult | null>(null);

    const pokemonQuery = useMemo(() => pokemonInput.trim().toLowerCase(), [pokemonInput]);

    const pokemonOptions = useMemo(() => {
        const q = pokemonQuery;
        if (!q) return [];

        const isDexSearch = /^\d+$/.test(q);
        if (isDexSearch) {
            return FULL_POKEMON.filter((p) =>
                String(Number(p.dex_id)).startsWith(String(Number(q))),
            );
        }

        return FULL_POKEMON.filter((p) =>
            p.name
                .toLowerCase()
                .split(/\s+/)
                .some((word) => word.startsWith(q)),
        );
    }, [pokemonQuery]);

    const selectedPokemon = useMemo(() => {
        if (pokemonId == null) return null;
        return FULL_POKEMON.find((p) => p.id === pokemonId) ?? null;
    }, [pokemonId]);

    const computedDiffs = useMemo(() => {
        const p = selectedPokemon;
        if (!p) return null;

        const computeOne = (stat: StatKey) => {
            const t = getTriplet(p, stat);
            const desiredValue = desired[stat];
            if (desiredValue <= t.min) return -4;
            return clampInt(desiredValue - t.base, -4, 4);
        };

        const d: Record<StatKey, number> = {
            speed: computeOne("speed"),
            power: computeOne("power"),
            skill: computeOne("skill"),
            stamina: computeOne("stamina"),
            jump: computeOne("jump"),
        };
        return d;
    }, [desired, selectedPokemon]);

    const allowedXValuesParsed = useMemo(
        () =>
            formValues.allowedXValues
                .split(",")
                .map((s) => parseInt(s.trim(), 10))
                .filter((n) => !isNaN(n) && n >= 1 && n <= 31),
        [formValues.allowedXValues],
    );

    const diffsLabel = useMemo(() => {
        if (!computedDiffs) return null;
        return STAT_ORDER.map((k) => {
            const v = computedDiffs[k];
            return v > 0 ? `+${v}` : String(v);
        }).join(", ");
    }, [computedDiffs]);

    const copy = useCallback(async (text: string) => {
        try {
            await navigator.clipboard.writeText(text);
        } catch {
            // ignore
        }
    }, []);

    const onSubmit = useCallback(
        async (e: FormEvent) => {
            e.preventDefault();
            setError(null);
            setResult(null);
            setLoading(true);
            try {
                if (!selectedPokemon || !computedDiffs) {
                    setError("Pick a Pokémon first.");
                    return;
                }
                const body: SolveRequest = {
                    mode: "diffs",
                    star_diffs: DIFFS_ORDER.map((k) => computedDiffs[k]),
                    compute_seed: formValues.computeSeed,
                    search_mode: formValues.searchMode,
                    allowed_x_values: allowedXValuesParsed.length > 0 ? allowedXValuesParsed : null,
                };
                const res = await postSolve(body);
                setResult(res.case);
            } catch (err) {
                setError(toErrorMessage(err));
            } finally {
                setLoading(false);
            }
        },
        [
            allowedXValuesParsed,
            computedDiffs,
            formValues.computeSeed,
            formValues.searchMode,
            selectedPokemon,
        ],
    );

    const onFormChange = useCallback(
        <K extends keyof SolverFormValues>(key: K, value: SolverFormValues[K]) => {
            dispatch({ key, value });
        },
        [],
    );

    const handlePokemonInputChange = useCallback(
        (value: string) => {
            setPokemonInput(value);

            const vv = value.trim().toLowerCase();
            if (!vv) {
                setPokemonId(null);
                return;
            }

            const digits = vv.match(/^\d+$/)?.[0];
            const byDex = digits
                ? FULL_POKEMON.find((p) => String(Number(p.dex_id)) === String(Number(digits)))
                : null;
            const byName = FULL_POKEMON.find((p) => p.name.toLowerCase() === vv);
            const byLabel = FULL_POKEMON.find(
                (p) => `${p.name} (#${dex3(p.dex_id)})`.toLowerCase() === vv,
            );
            const hit = byLabel ?? byName ?? byDex;
            if (hit) {
                setPokemonId(hit.id);
                setDesired(baseStars(hit));
            }
        },
        [setDesired, setPokemonId, setPokemonInput],
    );

    return (
        <>
            <PokemonPicker
                pokemonInput={pokemonInput}
                pokemonQuery={pokemonQuery}
                pokemonOptions={pokemonOptions}
                selectedPokemon={selectedPokemon}
                onInputChange={handlePokemonInputChange}
            />

            <StarEditor
                selectedPokemon={selectedPokemon}
                desired={desired}
                setDesired={setDesired}
                diffsLabel={diffsLabel}
            />

            <SolverForm
                values={formValues}
                onChange={onFormChange}
                loading={loading}
                isSubmitDisabled={!selectedPokemon}
                error={error}
                onSubmit={onSubmit}
            />

            <PokemonResult
                result={result}
                loading={loading}
                copy={copy}
                showAdvanced={formValues.showAdvanced}
                showSeed={formValues.computeSeed}
                topNSolutions={formValues.topNSolutions}
            />
        </>
    );
}

export default PokemonSearchMode;
