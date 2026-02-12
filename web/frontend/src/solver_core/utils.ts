import type { IntTuple, Nature, PokeathlonStats } from "./constants";
import { FEAS_MOD_TABLE, NATURES, ODD_INDEX } from "./constants";

export function reorderSpeedToStatFlavor(v: IntTuple): IntTuple {
    const [speed, power, skill, stamina, jump] = v;
    return [power, stamina, skill, jump, speed];
}

export function reorderStatFlavorToSpeed(v: IntTuple): IntTuple {
    const [power, stamina, skill, jump, speed] = v;
    return [speed, power, skill, stamina, jump];
}

export function pokemonToStarDiffs(
    desiredStarsSpeedOrder: IntTuple,
    pokemon: PokeathlonStats,
): IntTuple {
    const base = [pokemon.speed, pokemon.power, pokemon.skill, pokemon.stamina, pokemon.jump];
    const mins = [
        pokemon.speedMin,
        pokemon.powerMin,
        pokemon.skillMin,
        pokemon.staminaMin,
        pokemon.jumpMin,
    ];

    const diffsSpeedOrder: number[] = [];
    for (let i = 0; i < 5; i += 1) {
        const desired = desiredStarsSpeedOrder[i];
        const b = base[i];
        const mn = mins[i];
        if (desired <= mn) {
            diffsSpeedOrder.push(-4);
        } else {
            diffsSpeedOrder.push(desired - b);
        }
    }

    for (const x of diffsSpeedOrder) {
        if (x < -4 || x > 4) {
            throw new Error(
                "Computed star diff out of range [-4..4]; " +
                    `desired=${desiredStarsSpeedOrder}, base=${base}, mins=${mins}, diffs=${diffsSpeedOrder}`,
            );
        }
    }

    return reorderSpeedToStatFlavor(diffsSpeedOrder);
}

export function natureKey(nature: Nature): string {
    const [name, plusIdx, minusIdx, neutral] = nature;
    return `${name}|${plusIdx}|${minusIdx}|${neutral ? 1 : 0}`;
}

export const NATURE_TO_INDEX: Map<string, number> = new Map(
    NATURES.map((n, i) => [natureKey(n), i]),
);

export function isFeasible(nature: Nature, powerMod: number, staminaMod: number): boolean {
    const natIndex = NATURE_TO_INDEX.get(natureKey(nature));
    if (natIndex === undefined) return false;
    const p = ODD_INDEX[powerMod];
    const s = ODD_INDEX[staminaMod];
    if (p === undefined || s === undefined) return false;
    return ((FEAS_MOD_TABLE[natIndex][p] >> s) & 1) === 1;
}

export function weakestPenalty(
    flavs: number[],
    primary: number,
    secondary: number,
    mildness = 0,
): number {
    const sumStrongest = flavs[primary] + flavs[secondary];
    let decrease = 0;
    if (mildness < 200) {
        decrease = (sumStrongest * (100 - Math.floor(mildness / 25) * 10)) / 100;
    } else if (mildness < 255) {
        decrease = (sumStrongest * 20) / 100;
    } else {
        decrease = (sumStrongest * 10) / 100;
    }
    return Math.floor(decrease);
}

export function clampDailyRequirement(x: number): number | null {
    if (x <= -9) return -9;
    const req = x % 2 !== 0 ? x : x + 1;
    if (req > 9) return null;
    return req;
}
