import type { IntTuple, Nature } from "../constants";
import { clampDailyRequirement, weakestPenalty } from "../utils";

export function starToMinModifier(star: number): number {
    if (star < -4 || star > 4) {
        throw new Error(`Star bonus must be in [-4..4], got ${star}`);
    }

    if (star <= -4) return -(10 ** 9);
    if (star === -3) return -119;
    if (star === -2) return -79;
    if (star === -1) return -39;
    if (star === 0) return -14;
    if (star === 1) return 15;
    if (star === 2) return 40;
    if (star === 3) return 80;
    return 120;
}

export function applyNatureEffect(nature: Nature): number[] {
    const [, plusIdx, minusIdx, isNeutral] = nature;
    const delta = isNeutral ? 10 : 35;
    const eff = [0, 0, 0, 0, 0];
    eff[plusIdx] += delta;
    eff[minusIdx] -= delta;
    return eff;
}

export function applyRecipeEffect(flavors: IntTuple, mildness = 0): number[] {
    if (flavors.every((f) => f === 0)) return [0, 0, 0, 0, 0];

    const strongestIdx = flavors.reduce((best, val, i) => (val > flavors[best] ? i : best), 0);
    const weakestIdx = flavors.reduce(
        (best, val, i) => (val < flavors[best] || (val === flavors[best] && i > best) ? i : best),
        0,
    );

    const remaining = [0, 1, 2, 3, 4].filter((i) => i !== strongestIdx);
    const secondIdx = remaining.reduce(
        (best, i) => (flavors[i] > flavors[best] ? i : best),
        remaining[0],
    );

    const x = flavors[strongestIdx];
    const y = flavors[secondIdx];

    const mods = [0, 0, 0, 0, 0];
    mods[strongestIdx] += Math.floor(1.5 * x) + 10;
    mods[secondIdx] += Math.floor(1.5 * y);
    mods[weakestIdx] -= weakestPenalty(flavors, strongestIdx, secondIdx, mildness);

    return mods;
}

export function requiredDailyModifiers(
    desiredStars: IntTuple,
    baseModifiers: Iterable<number>,
): IntTuple | null {
    const mins = desiredStars.map((s) => starToMinModifier(s));
    const reqs: number[] = [];
    let idx = 0;
    for (const base of baseModifiers) {
        const need = mins[idx] - base;
        const req = clampDailyRequirement(need);
        if (req === null) return null;
        reqs.push(req);
        idx += 1;
    }
    return reqs;
}
