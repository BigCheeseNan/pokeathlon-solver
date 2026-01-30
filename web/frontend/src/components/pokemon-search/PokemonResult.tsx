import type { CaseResult } from "../../types";
import CaseView from "../common/CaseView";

type Props = {
    result: CaseResult | null;
    loading: boolean;
    copy: (t: string) => void;
    showAdvanced: boolean;
    topNSolutions: number | "";
};

function PokemonResult({
    result,
    loading,
    copy,
    showAdvanced,
    topNSolutions,
}: Props) {
    if (result) {
        return (
            <section className="results">
                <CaseView
                    c={result}
                    copy={copy}
                    showAdvanced={showAdvanced}
                    topN={topNSolutions}
                />
            </section>
        );
    }

    if (loading) {
        return (
            <section className="results">
                <div className="muted">
                    <span className="spinner" aria-hidden="true" /> Solving…
                </div>
            </section>
        );
    }

    return null;
}

export default PokemonResult;
