import type { StatKey } from "../../types";
import { STAT_ORDER } from "../../constants";
import { clampInt, getTriplet } from "../../utils/pokemon";
import StarRowRange from "../common/StarRowRange";
import type { FullPokemon } from "../../utils/pokemon";

type Props = {
    selectedPokemon: FullPokemon | null;
    desired: Record<StatKey, number>;
    setDesired: (
        v:
            | Record<StatKey, number>
            | ((prev: Record<StatKey, number>) => Record<StatKey, number>)
    ) => void;
    diffsLabel: string | null;
};

function StarEditor({
    selectedPokemon,
    desired,
    setDesired,
    diffsLabel,
}: Props) {
    if (!selectedPokemon) return null;

    return (
        <>
            <div className="starPicker">
                {STAT_ORDER.map((stat) => {
                    const t = getTriplet(selectedPokemon, stat);
                    return (
                        <StarRowRange
                            key={stat}
                            label={stat}
                            min={t.min}
                            base={t.base}
                            max={t.max}
                            value={desired[stat]}
                            onChange={(v) =>
                                setDesired((prev) => ({
                                    ...prev,
                                    [stat]: clampInt(v, t.min, t.max),
                                }))
                            }
                        />
                    );
                })}
            </div>
            {diffsLabel ? (
                <div className="muted">Difference to target stars: {diffsLabel}</div>
            ) : null}
        </>
    );
}

export default StarEditor;
