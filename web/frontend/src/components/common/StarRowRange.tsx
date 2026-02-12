import { useState } from "react";
import type { StatKey } from "../../types";
import { clampInt } from "../../utils/pokemon";
import StarIcon from "./StarIcon";

function StarRowRange({
    label,
    min,
    base,
    max,
    value,
    onChange,
}: {
    label: StatKey;
    min: number;
    base: number;
    max: number;
    value: number;
    onChange: (v: number) => void;
}) {
    const [hover, setHover] = useState<number | null>(null);
    const effective = clampInt(hover ?? value, min, max);

    return (
        <div className="starRow">
            <div className="starLabel">{label}</div>
            <div className="stars" onMouseLeave={() => setHover(null)}>
                {[1, 2, 3, 4, 5].map((n) => {
                    if (n > max) return null;
                    const clampedN = clampInt(n, min, max);

                    const filled = n <= effective;
                    const isMin = n <= min;
                    const isBase = n <= base;
                    const isBonus = filled && n > base;
                    const previewUp = hover !== null && clampedN > value && n <= clampedN;

                    let cls = "starIcon";
                    if (isMin) cls += " min";
                    else if (filled) cls += isBonus ? " filled bonus" : " filled";
                    if (filled && previewUp) cls += " preview";
                    if (isBase) cls += " base";

                    return (
                        <button
                            key={n}
                            type="button"
                            className="starBtn"
                            aria-label={`${label}: ${clampedN} star${clampedN === 1 ? "" : "s"}`}
                            onClick={() => onChange(clampedN)}
                            onMouseEnter={() => {
                                setHover(clampedN);
                            }}
                        >
                            <StarIcon className={cls} />
                        </button>
                    );
                })}
            </div>
        </div>
    );
}

export default StarRowRange;
