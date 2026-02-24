import type { Nature, PokeathlonStats } from "./constants";
import { FEAS_MOD_TABLE, NATURES, ODD_INDEX } from "./constants";

export function reorderSpeedToStatFlavor(v: number[]): number[] {
    const [speed, power, skill, stamina, jump] = v;
    return [power, stamina, skill, jump, speed];
}

export function reorderStatFlavorToSpeed(v: number[]): number[] {
    const [power, stamina, skill, jump, speed] = v;
    return [speed, power, skill, stamina, jump];
}

export function pokemonToStarDiffs(
    desiredStarsSpeedOrder: number[],
    pokemon: PokeathlonStats,
): number[] {
    const base = [pokemon.speed, pokemon.power, pokemon.skill, pokemon.stamina, pokemon.jump];
    const mins = [
        pokemon.speedMin,
        pokemon.powerMin,
        pokemon.skillMin,
        pokemon.staminaMin,
        pokemon.jumpMin,
    ];

    const diffsSpeedOrder = desiredStarsSpeedOrder.map((desired, i) => {
        const b = base[i];
        const mn = mins[i];
        return desired <= mn ? -4 : desired - b;
    });

    if (diffsSpeedOrder.some((x) => x < -4 || x > 4)) {
        throw new Error(
            "Computed star diff out of range [-4..4]; " +
                `desired=${desiredStarsSpeedOrder}, base=${base}, mins=${mins}, diffs=${diffsSpeedOrder}`,
        );
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
    extra = 0,
): number {
    const sumStrongest = flavs[primary] + flavs[secondary] + extra;
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

export function lexGreater(a1: number, a2: number, b1: number, b2: number): boolean {
    return a1 > b1 || (a1 === b1 && a2 > b2);
}

export function lexLess(a1: number, a2: number, b1: number, b2: number): boolean {
    return a1 < b1 || (a1 === b1 && a2 < b2);
}

export function lexGreaterOrEqual(a1: number, a2: number, b1: number, b2: number): boolean {
    return a1 > b1 || (a1 === b1 && a2 >= b2);
}

export function lexLessOrEqual(a1: number, a2: number, b1: number, b2: number): boolean {
    return a1 < b1 || (a1 === b1 && a2 <= b2);
}
