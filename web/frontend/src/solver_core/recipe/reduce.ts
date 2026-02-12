import type { IntTuple } from "../constants";
import { EFFECTS, MAX_FLAVOR, MAX_TOTAL } from "../constants";

export function applyIngredient(flavors: IntTuple, ingredient: string): number[] {
    const [effect, candidates] = EFFECTS[ingredient];
    const newFlavors = [0, 0, 0, 0, 0];
    for (let i = 0; i < 5; i += 1) {
        const val = flavors[i] + effect[i];
        if (val < 0) newFlavors[i] = 0;
        else if (val > MAX_FLAVOR) newFlavors[i] = MAX_FLAVOR;
        else newFlavors[i] = val;
    }
    const total = newFlavors.reduce((a, b) => a + b, 0);
    if (total > MAX_TOTAL) {
        const idx = candidates.reduce(
            (best, i) => (newFlavors[i] > newFlavors[best] ? i : best),
            candidates[0],
        );
        newFlavors[idx] = Math.max(0, newFlavors[idx] + MAX_TOTAL - total);
    }
    return newFlavors;
}

export function flavorsMatch(f1: IntTuple, f2: IntTuple): boolean {
    for (let i = 0; i < 5; i += 1) if (f1[i] !== f2[i]) return false;
    return true;
}

export function swapGroups(
    grouped: Array<[string, number]>,
    i: number,
    j: number,
): Array<[string, number]> {
    const out = grouped.slice();
    const tmp = out[i];
    out[i] = out[j];
    out[j] = tmp;
    return out;
}

export function isValidGrouping(grouped: Array<[string, number]>, target: IntTuple): boolean {
    let current: number[] = [0, 0, 0, 0, 0];
    for (const [ing, cnt] of grouped) {
        for (let k = 0; k < cnt; k += 1) {
            if (ing === "strong" && current.reduce((a, b) => a + b, 0) > MAX_TOTAL - 10) {
                return false;
            }
            current = applyIngredient(current, ing);
        }
    }
    return flavorsMatch(current, target);
}

export function reduceRecipe(recipe: string[], target: IntTuple): Array<[string, number]> {
    if (recipe.length === 0) return [];

    const grouped: Array<[string, number]> = [];
    let current = recipe[0];
    let count = 1;
    for (let i = 1; i < recipe.length; i += 1) {
        if (recipe[i] === current) count += 1;
        else {
            grouped.push([current, count]);
            current = recipe[i];
            count = 1;
        }
    }
    grouped.push([current, count]);

    let i = 0;
    while (i < grouped.length - 2) {
        const curr = grouped[i][0];
        const candidates = grouped
            .map((g, idx) => [idx, g] as const)
            .filter(([idx, g]) => g[0] === curr && idx > i);
        for (const [j] of candidates) {
            const newGrouped = swapGroups(grouped, i + 1, j);
            if (isValidGrouping(newGrouped, target)) {
                grouped.splice(0, grouped.length, ...newGrouped);
                i += 1;
            }
        }
        i += 1;
    }

    const merged: Array<[string, number]> = [];
    let prevIng = grouped[0][0];
    let accCnt = grouped[0][1];
    for (const [ing, cnt] of grouped.slice(1)) {
        if (ing === prevIng) accCnt += cnt;
        else {
            merged.push([prevIng, accCnt]);
            prevIng = ing;
            accCnt = cnt;
        }
    }
    merged.push([prevIng, accCnt]);
    return merged;
}
