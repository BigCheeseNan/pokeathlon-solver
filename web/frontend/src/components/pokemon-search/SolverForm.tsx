import type { FormEvent } from "react";

export type SolverFormValues = {
    computeSeed: boolean;
    searchMode: "min" | "max";
    allowedXValues: string;
    showAdvanced: boolean;
    topNSolutions: number | "";
};

type Props = {
    values: SolverFormValues;
    onChange: <K extends keyof SolverFormValues>(
        key: K,
        value: SolverFormValues[K]
    ) => void;
    loading: boolean;
    isSubmitDisabled: boolean;
    error: string | null;
    onSubmit: (e: FormEvent) => void;
};

function SolverForm({
    values,
    onChange,
    loading,
    isSubmitDisabled,
    error,
    onSubmit,
}: Props) {
    return (
        <form className="panel" onSubmit={onSubmit}>
            <div className="row">
                <label className="label">Compute PID/seed</label>
                <input
                    type="checkbox"
                    checked={values.computeSeed}
                    onChange={(e) =>
                        onChange("computeSeed", e.target.checked)
                    }
                />
            </div>
            <div className="row">
                <label className="label">Search mode</label>
                <select
                    value={values.searchMode}
                    onChange={(e) =>
                        onChange("searchMode", e.target.value as "min" | "max")
                    }
                >
                    <option value="min">Min ingredients</option>
                    <option value="max">Better seeds</option>
                </select>
            </div>
            <div className="row">
                <label className="label">Required days (1-31)</label>
                <input
                    type="text"
                    placeholder="e.g., 1,5,10 (leave empty for all)"
                    value={values.allowedXValues}
                    onChange={(e) => onChange("allowedXValues", e.target.value)}
                />
            </div>
            <div className="row">
                <label className="label">Show advanced info</label>
                <input
                    type="checkbox"
                    checked={values.showAdvanced}
                    onChange={(e) =>
                        onChange("showAdvanced", e.target.checked)
                    }
                />
            </div>
            <div className="row">
                <label className="label">Top N solutions</label>
                <input
                    type="number"
                    min={1}
                    placeholder="(all)"
                    value={values.topNSolutions}
                    onChange={(e) => {
                        const v = e.target.value;
                        onChange("topNSolutions", v === "" ? "" : Number(v));
                    }}
                />
            </div>

            <div className="row">
                <button
                    className="primary"
                    type="submit"
                    disabled={loading || isSubmitDisabled}
                >
                    {loading ? "Solving…" : "Solve"}
                </button>
            </div>

            {error ? <div className="error">{error}</div> : null}
        </form>
    );
}

export default SolverForm;
