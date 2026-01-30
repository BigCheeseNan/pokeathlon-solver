import { useState } from "react";
import StarIcon from "./StarIcon";

function StarRow({
    label,
    value,
    onChange,
}: {
    label: string;
    value: number;
    onChange: (v: number) => void;
}) {
    const [hover, setHover] = useState<number | null>(null);
    const effective = hover ?? value;

    return (
        <div className="starRow">
            <div className="starLabel">{label}</div>
            <div
                className="stars"
                role="radiogroup"
                aria-label={`${label} stars`}
                onMouseLeave={() => setHover(null)}
            >
                {[1, 2, 3, 4, 5].map((n) => {
                    const filled = n <= effective;
                    const preview = hover !== null && n > value && n <= hover;
                    const cls = filled
                        ? preview
                            ? "starIcon filled preview"
                            : "starIcon filled"
                        : "starIcon";

                    return (
                        <button
                            key={n}
                            type="button"
                            className="starBtn"
                            role="radio"
                            aria-checked={n === value}
                            aria-label={`${label}: ${n} star${
                                n === 1 ? "" : "s"
                            }`}
                            onClick={() => onChange(n)}
                            onMouseEnter={() => setHover(n)}
                        >
                            <StarIcon className={cls} />
                        </button>
                    );
                })}
            </div>
        </div>
    );
}

export default StarRow;
