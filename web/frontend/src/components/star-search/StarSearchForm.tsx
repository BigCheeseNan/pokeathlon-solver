import { type FormEvent } from "react";
import StarRow from "../common/StarRow";

export type StarFormValues = {
    stars: number[];
    pokemonTopN: number;
    computeSeed: boolean;
    searchMode: "min" | "max";
    allowedXValues: string;
    topNSolutions: number | "";
    showAdvanced: boolean;
};

type Props = {
    starLabels: string[];
    values: StarFormValues;
    onChange: <K extends keyof StarFormValues>(
        key: K,
        value: StarFormValues[K]
    ) => void;
    isSearching: boolean;
    error: string | null;
    onSubmit: (e: FormEvent) => void;
};

function StarSearchForm({
    starLabels,
    values,
    onChange,
    isSearching,
    error,
    onSubmit,
}: Props) {
    return (
        <form className="panel" onSubmit={onSubmit}>
            <div className="starPicker">
                {starLabels.map((lbl, i) => (
                    <StarRow
                        key={lbl}
                        label={lbl}
                        value={values.stars[i]}
                        onChange={(v) =>
                            onChange(
                                "stars",
                                values.stars.map((val, idx) =>
                                    idx === i ? v : val
                                )
                            )
                        }
                    />
                ))}
            </div>
            <div className="row">
                <label className="label">Top N Pokemon</label>
                <input
                    type="number"
                    min={1}
                    max={200}
                    value={values.pokemonTopN}
                    onChange={(e) =>
                        onChange("pokemonTopN", Number(e.target.value))
                    }
                />
            </div>

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
                        onChange(
                            "searchMode",
                            e.target.value as "min" | "max"
                        )
                    }
                >
                    <option value="min">Min ingredients</option>
                    <option value="max">Better seeds</option>
                </select>
            </div>
            <div className="row">
                <label className="label">Allowed days (1-31)</label>
                <input
                    type="text"
                    placeholder="e.g., 1,5,10 (leave empty for all)"
                    value={values.allowedXValues}
                    onChange={(e) =>
                        onChange("allowedXValues", e.target.value)
                    }
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
                <button className="primary" type="submit" disabled={isSearching}>
                    {isSearching ? "Searching…" : "Solve"}
                </button>
            </div>

            {error ? <div className="error">{error}</div> : null}
        </form>
    );
}

export default StarSearchForm;
