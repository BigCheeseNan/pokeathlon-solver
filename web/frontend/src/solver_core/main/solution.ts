import type { Nature, Solution } from "../constants";
import { NATURES, PAIRS_PREFER_POWER, PAIRS_PREFER_STAMINA } from "../constants";
import { findFlavors } from "./flavors";
import {
    applyNatureEffect,
    applyRecipeEffect,
    requiredDailyModifiers,
    starToMinModifier,
} from "./modifiers";
import { isFeasible } from "../utils";

function solveForNature(
    desiredStars: number[],
    nat: Nature,
    mode: "min" | "max" = "min",
): Solution | null {
    let dailyMods = [-9, -9, -9, -9, -9];
    if (mode === "min") {
        dailyMods = [9, 9, 9, 9, 9];
        const pairsByPriority =
            desiredStars[0] < desiredStars[1] ? PAIRS_PREFER_POWER : PAIRS_PREFER_STAMINA;

        const pair = pairsByPriority.find(([, p, s]) => isFeasible(nat, p, s));
        if (!pair) return null;
        const [, p, s] = pair;
        dailyMods[0] = p;
        dailyMods[1] = s;
    }

    const modifiers = dailyMods;
    const [, plusIdx, minusIdx, isNeutral] = nat;
    modifiers[plusIdx] += isNeutral ? 10 : 35;
    modifiers[minusIdx] += isNeutral ? -10 : -35;

    const res = findFlavors(desiredStars, modifiers, mode);
    if (!res) return null;
    const [flavors, mildness] = res;

    if (flavors.reduce((a, b) => a + b, 0) > 100) {
        throw new Error(`Flavor sum exceeds 100: ${flavors}`);
    }
    if (flavors.some((f) => f > 63)) {
        throw new Error(`Flavor exceeds per-flavor cap 63: ${flavors}, mode=${mode}`);
    }

    const recipeModifiers = applyRecipeEffect(flavors, mildness);
    recipeModifiers[plusIdx] += isNeutral ? 10 : 35;
    recipeModifiers[minusIdx] += isNeutral ? -10 : -35;

    const minDailyMods = requiredDailyModifiers(desiredStars, recipeModifiers);
    if (!minDailyMods) return null;

    for (let i = 0; i < 5; i++) {
        if (minDailyMods[i] + recipeModifiers[i] < starToMinModifier(desiredStars[i])) return null;
    }

    return {
        nature: nat,
        flavors,
        recipe_effect: applyRecipeEffect(flavors, mildness),
        nature_effect: applyNatureEffect(nat),
        required_daily: minDailyMods,
        mildness,
    };
}

export function findAllSolutions(desiredStars: number[], mode: "min" | "max" = "min"): Solution[] {
    const positiveStars = desiredStars.map((s, i) => [i, s] as const).filter(([, s]) => s > 0);
    const negativeStars = desiredStars.map((s, i) => [i, s] as const).filter(([, s]) => s < 0);

    if (positiveStars.length > 3) return [];
    if (Math.max(...desiredStars) > 3 && positiveStars.length > 2) return [];
    if (desiredStars.filter((s) => s === 4).length > 1) return [];
    if (positiveStars.reduce((sum, [, s]) => sum + s, 0) > 8) return [];
    if (desiredStars.filter((s) => s === 4).length === 1 && negativeStars.length === 0) return [];

    const forced4Idx = desiredStars.indexOf(4);

    const results: Solution[] = [];
    for (const nat of NATURES) {
        if (forced4Idx !== -1 && (nat[3] || nat[1] !== forced4Idx)) continue;
        const sol = solveForNature(desiredStars, nat, mode);
        if (sol) results.push(sol);
    }
    return results;
}
