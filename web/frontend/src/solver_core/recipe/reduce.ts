import { EFFECTS, MAX_FLAVOR, MAX_TOTAL } from "../constants";

export function applyIngredient(flavors: number[], ingredient: string): number[] {
    const [effect, candidates] = EFFECTS[ingredient];
    const newFlavors = [0, 0, 0, 0, 0];
    for (let i = 0; i < 5; i++) {
        const val = flavors[i] + effect[i];
        if (val < 0) newFlavors[i] = 0;
        else if (val > MAX_FLAVOR) newFlavors[i] = MAX_FLAVOR;
        else newFlavors[i] = val;
    }
    const total = newFlavors.reduce((a, b) => a + b, 0);
    if (total > MAX_TOTAL) {
        const idx = candidates.reduce((best, i) => {
            return newFlavors[i] > newFlavors[best] ? i : best;
        }, candidates[0]);
        newFlavors[idx] = Math.max(0, newFlavors[idx] + MAX_TOTAL - total);
    }
    return newFlavors;
}

export function flavorsMatch(f1: number[], f2: number[]): boolean {
    return f1.every((val, i) => val === f2[i]);
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

export function isValidGrouping(grouped: Array<[string, number]>, target: number[]): boolean {
    let current: number[] = [0, 0, 0, 0, 0];
    for (const [ing, cnt] of grouped) {
        for (let k = 0; k < cnt; k++) {
            const sum = current.reduce((a, b) => a + b, 0);
            if (ing === "strong" && sum > MAX_TOTAL - 10) return false;
            current = applyIngredient(current, ing);
        }
    }
    return flavorsMatch(current, target);
}

export function reduceRecipe(recipe: string[], target: number[]): Array<[string, number]> {
    if (recipe.length === 0) return [];

    let grouped = recipe.reduce<Array<[string, number]>>((acc, ingredient) => {
        const lastGroup = acc[acc.length - 1];
        if (lastGroup && lastGroup[0] === ingredient) {
            lastGroup[1]++;
        } else {
            acc.push([ingredient, 1]);
        }
        return acc;
    }, []);

    let cursor = 0;
    while (cursor < grouped.length - 2) {
        const curr = grouped[cursor][0];
        const candidateIndexes = grouped
            .map(([ingredient], idx) => (idx > cursor && ingredient === curr ? idx : -1))
            .filter((idx) => idx !== -1);

        for (const candidateIndex of candidateIndexes) {
            const newGrouped = swapGroups(grouped, cursor + 1, candidateIndex);
            if (isValidGrouping(newGrouped, target)) {
                grouped = newGrouped;
                cursor++;
            }
        }
        cursor++;
    }

    return grouped.reduce<Array<[string, number]>>((acc, [ingredient, count]) => {
        const lastGroup = acc[acc.length - 1];
        if (lastGroup && lastGroup[0] === ingredient) {
            lastGroup[1] += count;
        } else {
            acc.push([ingredient, count]);
        }
        return acc;
    }, []);
}
