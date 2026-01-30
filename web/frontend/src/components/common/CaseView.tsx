import type { CaseResult } from "../../types";
import { reorderDiffsToStats, hex32 } from "../../utils/pokemon";

function CaseView({
    c,
    copy,
    showAdvanced,
    topN,
}: {
    c: CaseResult;
    copy: (t: string) => void;
    showAdvanced: boolean;
    topN: number | "";
}) {
    const displayedResults = topN === "" ? c.results : c.results.slice(0, topN);

    return (
        <div>
            {c.label ? <h3>{c.label}</h3> : null}
            {showAdvanced ? (
                <div className="meta">
                    <div>
                        <b>Difference to target stars (speed, power, skill, stamina, jump)</b>: {" "}
                        {reorderDiffsToStats(c.desired_star_diffs)
                            .map((d) => (d > 0 ? `+${d}` : d.toString()))
                            .join(", ")}
                    </div>
                    <div>
                        <b>Possible Natures</b>: {c.solutions_total} |{" "}
                        <b>With recipes</b>: {c.solutions_with_recipes} |{" "}
                        <b>Recipe failures</b>: {c.recipe_failures} |{" "}
                        <b>Invalid PIDs</b>: {c.invalid_seeds}
                    </div>
                </div>
            ) : null}

            {c.error ? <div className="warn">{c.error}</div> : null}

            {topN !== "" && c.results.length > topN ? (
                <div className="muted">
                    Showing top {topN} of {c.results.length} solutions
                </div>
            ) : null}

            <div className="cards">
                {displayedResults.map((r, idx) => (
                    <div key={idx} className="card">
                        <div className="cardTop">
                            <div>
                                <b>#{idx + 1}</b> nature: ({r.nature.index}){" "}
                                {r.nature.name} (+{r.nature.plus}, -
                                {r.nature.minus}
                                {showAdvanced ? `, Δ=${r.nature.delta}` : ""})
                            </div>
                        </div>
                        <div className="kv">
                            {showAdvanced ? (
                                <>
                                    <div>
                                        <b>Required daily (speed, power, skill, stamina, jump)</b>: {" "}
                                        {reorderDiffsToStats(r.required_daily).join(", ")}{" "}
                                        {`total=${r.daily_sum}`}
                                    </div>
                                    <div>
                                        <b>Flavors</b>: {r.flavors.join(", ")}
                                    </div>
                                </>
                            ) : null}
                            <div>
                                <b>Ingredients</b>: {" "}
                                {r.grouped_ingredients.length
                                    ? r.grouped_ingredients
                                          .map(
                                              (g) =>
                                                  `${g.ingredient} x${g.count}`
                                          )
                                          .join(", ")
                                    : "No aprijuice needed"}
                                {showAdvanced
                                    ? ` (total=${r.ingredients})`
                                    : ""}
                                {(r.mildness > 0 || showAdvanced) && (
                                    <span>
                                        {" "} | <b>Mildness</b>: {r.mildness}
                                    </span>
                                )}
                            </div>
                            {r.seed_result ? (
                                <div className="seed">
                                    <div>
                                        <b>PID</b>: {hex32(r.seed_result.pid)}{" "}
                                        <button
                                            className="mini"
                                            onClick={() =>
                                                copy(
                                                    hex32(
                                                        r.seed_result!.pid
                                                    ).slice(2)
                                                )
                                            }
                                        >
                                            copy
                                        </button>
                                    </div>
                                    <div>
                                        <b>Seed</b>: {hex32(r.seed_result.seed)}{" "}
                                        <button
                                            className="mini"
                                            onClick={() =>
                                                copy(
                                                    hex32(
                                                        r.seed_result!.seed
                                                    ).slice(2)
                                                )
                                            }
                                        >
                                            copy
                                        </button>
                                    </div>
                                    <div>
                                        <b>Valid days</b>: {" "}
                                        {r.seed_result.days.length == 31
                                            ? "All days"
                                            : r.seed_result.days.join(", ")}
                                        {showAdvanced
                                            ? ` (streak=${r.seed_result.streak}, count=${r.seed_result.count})`
                                            : ""}
                                    </div>
                                    {showAdvanced ? (
                                        <div>
                                            <b>Natural catch odds</b>: {" "}
                                            {parseFloat(
                                                (
                                                    r.seed_result
                                                        .natural_catch_probability *
                                                    2500
                                                ).toFixed(2)
                                            ).toString()}
                                            %
                                            {` (num_offsets=${r.seed_result.num_offsets})`}
                                        </div>
                                    ) : null}
                                </div>
                            ) : (
                                <div className="muted">PID/seed impossible</div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default CaseView;
