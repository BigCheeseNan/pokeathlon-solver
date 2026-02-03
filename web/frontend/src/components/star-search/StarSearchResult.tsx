import type { CaseResult, PokemonCandidate } from "../../types";
import CaseView from "../common/CaseView";

type Props = {
    result: CaseResult | null;
    isSolving: boolean;
    selectedPokemon: PokemonCandidate | null;
    copy: (t: string) => void;
    showAdvanced: boolean;
    showSeed: boolean;
    topNSolutions: number | "";
};

function StarSearchResult({
    result,
    isSolving,
    selectedPokemon,
    copy,
    showAdvanced,
    showSeed,
    topNSolutions,
}: Props) {
    if (result) {
        return (
            <div className="caseBlock">
                <CaseView
                    c={result}
                    copy={copy}
                    showAdvanced={showAdvanced}
                    showSeed={showSeed}
                    topN={topNSolutions}
                />
            </div>
        );
    }

    if (isSolving && selectedPokemon) {
        return (
            <div className="muted">
                <span className="spinner" aria-hidden="true" /> Solving…
            </div>
        );
    }

    return <div className="muted">Click a Pokemon to run the solver</div>;
}

export default StarSearchResult;
