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
    onChange: <K extends keyof SolverFormValues>(key: K, value: SolverFormValues[K]) => void;
    loading: boolean;
    isSubmitDisabled: boolean;
    error: string | null;
    onSubmit: (e: FormEvent) => void;
};

function SolverForm({ values, onChange, loading, isSubmitDisabled, error, onSubmit }: Props) {
    return (
        <form className="panel" onSubmit={onSubmit}>
            <div
                className="row"
                title="Whether to show the PID/seed for RNG manipulation (check natural catch odds in advanced info to see if needed)"
            >
                <label className="label">Compute PID/seed</label>
                <input
                    type="checkbox"
                    checked={values.computeSeed}
                    onChange={(e) => onChange("computeSeed", e.target.checked)}
                />
            </div>
            <div
                className="row"
                title="Min ingredients minimizes apricorns used in the recipe at the cost of introducing more constraints on PID
Better Seeds finds a recipe that minimizes the constraints on the PID (use this if you don't want to use RNG manip)"
            >
                <label className="label">Search mode</label>
                <select
                    value={values.searchMode}
                    onChange={(e) => onChange("searchMode", e.target.value as "min" | "max")}
                >
                    <option value="min">Min ingredients</option>
                    <option value="max">Better seeds</option>
                </select>
            </div>
            <div
                className="row"
                title="Use this to force the PID to work on specific days (useful when you need different Pokemon on the same team)"
            >
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
                    onChange={(e) => onChange("showAdvanced", e.target.checked)}
                />
            </div>
            <div
                className="row"
                title="The maximum number of solutions (natures) to return. Leave empty to return all"
            >
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
                <button className="primary" type="submit" disabled={loading || isSubmitDisabled}>
                    {loading ? "Solving…" : "Solve"}
                </button>
            </div>

            {error ? <div className="error">{error}</div> : null}
        </form>
    );
}

export default SolverForm;
