import { starToMinModifier } from "./modifiers";
import { lexGreater, lexGreaterOrEqual, lexLess, lexLessOrEqual, weakestPenalty } from "../utils";

function minRequiredMildness(
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
    desiredStars: number[],
    modifiers: number[],
    mode: "min" | "max" = "min",
): [number[], number] | null {
    const diffs = desiredStars.map((s, i) => starToMinModifier(s) - modifiers[i]);
    let flavors = [0, 0, 0, 0, 0];

    if (diffs.every((d) => d <= 0)) return [flavors, 0];

    let [secondIdx, maxIdx] = [0, 1, 2, 3, 4]
        .sort((a, b) => diffs[a] - diffs[b] || b - a)
        .slice(-2);

    const maxDiff = diffs[maxIdx];
    const secondDiff = diffs[secondIdx];

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
        maxFlav++;
        if (maxFlav + secondFlav > 100) secondFlav--;
    }

    flavors[secondIdx] = secondFlav;
    flavors[maxIdx] = maxFlav;

    let decrease = maxFlav + secondFlav;

    let decreaseIdx = null;
    for (let i = 4; i >= 0; i--) {
        if (decrease <= -diffs[i]) {
            decreaseIdx = i;
            break;
        }
    }

    decreaseIdx ??= diffs.reduce((best, d, i) => {
        return lexLess(d, -i, diffs[best], -best) ? i : best;
    }, 0);

    flavors = flavors.map((flavor, i) => (i > decreaseIdx && !flavor ? flavor + 1 : flavor));

    let sum = flavors.reduce((a, b) => a + b, 0);
    if (sum === 102) {
        flavors[secondIdx]--;
        flavors[maxIdx]--;
    } else if (sum === 101) {
        if (lexGreaterOrEqual(maxFlav - secondFlav, secondIdx, 1, maxIdx)) {
            flavors[maxIdx]--;
        } else {
            flavors[secondIdx]--;
        }
    }

    const mildness = minRequiredMildness(diffs, maxFlav, secondFlav, decreaseIdx);

    const canAdd = (i: number, d: number): boolean => {
        sum = flavors.reduce((a, b) => a + b, 0);
        secondIdx = [0, 1, 2, 3, 4].sort((a, b) => flavors[a] - flavors[b] || b - a)[3];
        const isLargest = i === maxIdx || i === secondIdx;
        if (sum + d > 100 || flavors[i] % (d * 2) === 0 || flavors[i] > 61) return false;
        decrease = weakestPenalty(flavors, maxIdx, secondIdx, mildness, d);
        if (isLargest && decrease > -diffs[decreaseIdx]) return false;
        if (i !== maxIdx && lexGreater(flavors[i] + d, maxIdx, flavors[maxIdx], i)) return false;
        return isLargest || lexLessOrEqual(flavors[i] + d, secondIdx, flavors[secondIdx], i);
    };

    for (const delta of [1, 2, 1, 2]) {
        for (let i = 0; i < 5; i += 1) {
            if (canAdd(i, delta)) flavors[i] += delta;
        }
    }
    return [flavors, mildness];
}
