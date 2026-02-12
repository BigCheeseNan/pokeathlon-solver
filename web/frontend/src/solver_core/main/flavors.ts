import type { IntTuple } from "../constants";
import { starToMinModifier } from "./modifiers";
import { weakestPenalty } from "../utils";

export function minRequiredMildness(
    diffs: number[],
    maxFlav: number,
    secondFlav: number,
    decreaseIdx: number,
): number {
    const minDiff = diffs[decreaseIdx];
    const decrease = maxFlav + secondFlav;
    if (decrease <= -minDiff) return 0;
    for (let mildness = 0; mildness < 200; mildness += 25) {
        const adjusted = Math.floor((decrease * (100 - Math.floor(mildness / 25) * 10)) / 100);
        if (adjusted <= -minDiff) return mildness;
    }
    if (Math.floor((decrease * 20) / 100) <= -minDiff) return 200;
    return 255;
}

export function findFlavors(
    desiredStars: IntTuple,
    modifiers: number[],
    mode: "min" | "max" = "min",
): [IntTuple, number] | null {
    const diffs = desiredStars.map((s, i) => starToMinModifier(s) - modifiers[i]);
    const flavors = [0, 0, 0, 0, 0];

    if (diffs.every((d) => d <= 0)) return [flavors, 0];

    const indices = [0, 1, 2, 3, 4].sort((a, b) => {
        if (diffs[a] === diffs[b]) return b - a;
        return diffs[a] - diffs[b];
    });
    let secondIdx = indices[3];
    const maxIdx = indices[4];

    const maxDiff = diffs[maxIdx];
    const secondDiff = diffs[secondIdx];

    let mildness = 0;
    let secondFlav = 0;
    let maxFlav = 0;

    if (mode === "min") {
        secondFlav = Math.max(0, Math.ceil(secondDiff / 1.5));
        maxFlav = Math.max(Math.ceil((maxDiff - 10) / 1.5), secondFlav);
    } else {
        secondFlav = Math.min(Math.max(0, Math.ceil(secondDiff / 1.5)), 50);
        maxFlav = Math.min(
            Math.max(Math.ceil((maxDiff - 10) / 1.5), secondFlav),
            Math.min(100 - secondFlav, 63),
        );
    }

    if (mode === "min" && (maxFlav > 63 || maxFlav + secondFlav > 100)) return null;
    if (maxIdx > secondIdx && maxFlav === secondFlav) {
        maxFlav += 1;
        if (mode !== "min" && maxFlav + secondFlav > 100) secondFlav -= 1;
    }

    flavors[secondIdx] = secondFlav;
    flavors[maxIdx] = maxFlav;

    let decrease = weakestPenalty(flavors, maxIdx, secondIdx, mildness);

    let decreaseIdx = null;
    for (let i = 4; i >= 0; i--) {
        if (decrease <= -diffs[i]) {
            decreaseIdx = i;
            break;
        }
    }

    decreaseIdx ??= [0, 1, 2, 3, 4].reduce((best, i) => {
        if (diffs[i] < diffs[best]) return i;
        if (diffs[i] === diffs[best] && i > best) return i;
        return best;
    }, 0);

    for (let i = 4; i > decreaseIdx; i--) {
        if (flavors[i] === 0) {
            flavors[i] += 1;
        }
    }

    const total = flavors.reduce((a, b) => a + b, 0);
    if (total === 102) {
        flavors[secondIdx] -= 1;
        flavors[maxIdx] -= 1;
    } else if (total === 101) {
        if (maxFlav - secondFlav > 0 || (maxFlav - secondFlav === 0 && secondIdx >= maxIdx)) {
            flavors[maxIdx] -= 1;
        } else {
            flavors[secondIdx] -= 1;
        }
    }

    const canAdd = (i: number, delta: number): boolean => {
        const sum = flavors.reduce((a, b) => a + b, 0);
        if (sum + delta > 100 || flavors[i] % (delta * 2) === 0 || flavors[i] > 61) {
            return false;
        }
        secondIdx = [...flavors].map((f, i) => ({ i, f })).sort((a, b) => b.f - a.f)[1].i;
        const dec = weakestPenalty(flavors, maxIdx, secondIdx, mildness);
        if (i === maxIdx || i === secondIdx) {
            if (dec + delta > -diffs[decreaseIdx]) return false;
        }
        if (
            i !== maxIdx &&
            (flavors[i] + delta > flavors[maxIdx] ||
                (flavors[i] + delta === flavors[maxIdx] && maxIdx > i))
        ) {
            return false;
        }
        return (
            i === maxIdx ||
            i === secondIdx ||
            flavors[i] + delta < flavors[secondIdx] ||
            (flavors[i] + delta === flavors[secondIdx] && secondIdx <= i)
        );
    };

    for (const delta of [1, 2, 1, 2]) {
        for (let i = 0; i < 5; i += 1) {
            if (canAdd(i, delta)) flavors[i] += delta;
        }
    }

    mildness = minRequiredMildness(diffs, maxFlav, secondFlav, decreaseIdx);
    return [flavors, mildness];
}
