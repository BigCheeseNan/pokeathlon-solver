import type { FlavorKey, StatKey } from "./types";

export const STAT_ORDER: StatKey[] = [
    "speed",
    "power",
    "skill",
    "stamina",
    "jump",
];
export const DIFFS_ORDER: StatKey[] = [
    "power",
    "stamina",
    "skill",
    "jump",
    "speed",
];

export const FlavorsToColor: Record<FlavorKey, string> = {
    sweet: "pink",
    spicy: "red",
    dry: "blue",
    bitter: "green",
    sour: "yellow",
    strong: "black",
    mild: "white",
};