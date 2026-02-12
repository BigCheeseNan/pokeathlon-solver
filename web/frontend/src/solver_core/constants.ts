export type IntTuple = number[];
export type FiveTuple = [number, number, number, number, number];

export type Nature = [string, number, number, boolean];

export const STAT_FLAVOR = ["power", "stamina", "skill", "jump", "speed"] as const;
export const FLAVOR_LABELS = ["spicy", "sour", "dry", "bitter", "sweet"] as const;
export const INGREDIENTS = ["spicy", "sour", "dry", "bitter", "sweet", "mild", "strong"] as const;

export type FlavorKey = (typeof INGREDIENTS)[number];

export const STAT_ORDER_SPEED_FIRST = ["speed", "power", "skill", "stamina", "jump"] as const;

export const MAX_FLAVOR = 63;
export const MAX_TOTAL = 100;

export const EFFECTS: Record<string, [FiveTuple, number[]]> = {
    spicy: [
        [4, -2, 0, 0, 0],
        [1, 2, 3, 4],
    ],
    sour: [
        [0, 4, -2, 0, 0],
        [0, 2, 3, 4],
    ],
    dry: [
        [0, 0, 4, -2, 0],
        [0, 1, 3, 4],
    ],
    bitter: [
        [0, 0, 0, 4, -2],
        [0, 1, 2, 4],
    ],
    sweet: [
        [-2, 0, 0, 0, 4],
        [0, 1, 2, 3],
    ],
    mild: [[-2, -2, -2, -2, -2], []],
    strong: [[2, 2, 2, 2, 2], []],
};

export const MIN_STAR_BONUS = -4;
export const MAX_STAR_BONUS = 4;
export const MIN_DAILY_MOD = -9;
export const MAX_DAILY_MOD = 9;

export const NATURES: Nature[] = [
    ["Hardy", 0, 4, true],
    ["Lonely", 0, 1, false],
    ["Brave", 0, 4, false],
    ["Adamant", 0, 3, false],
    ["Naughty", 0, 2, false],
    ["Bold", 1, 0, false],
    ["Docile", 1, 3, true],
    ["Relaxed", 1, 4, false],
    ["Impish", 1, 3, false],
    ["Lax", 1, 2, false],
    ["Timid", 4, 0, false],
    ["Hasty", 4, 1, false],
    ["Serious", 4, 2, true],
    ["Jolly", 4, 3, false],
    ["Naive", 4, 2, false],
    ["Modest", 3, 0, false],
    ["Mild", 3, 1, false],
    ["Quiet", 3, 4, false],
    ["Bashful", 3, 0, true],
    ["Rash", 3, 2, false],
    ["Calm", 2, 0, false],
    ["Gentle", 2, 1, false],
    ["Sassy", 2, 4, false],
    ["Careful", 2, 3, false],
    ["Quirky", 2, 1, true],
];

export const ODD_TARGETS = [-9, -7, -5, -3, -1, 1, 3, 5, 7, 9] as const;
export const ODD_INDEX: Record<number, number> = Object.fromEntries(
    ODD_TARGETS.map((v, i) => [v, i]),
);

export const FEAS_MOD_TABLE: number[][] = [
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 255, 0, 0],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 255, 0],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 255],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023],
    [1023, 1023, 1023, 1023, 1023, 1023, 511, 511, 511, 511],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 511, 0, 0],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 511, 0],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 511],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023],
    [1023, 1023, 1023, 1023, 1023, 1023, 511, 511, 511, 511],
    [1023, 1023, 1023, 1023, 1023, 1023, 511, 511, 0, 0],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 511, 511, 0],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 511, 511],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 255],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 0, 0],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 0],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 511],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 0, 0],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 0],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023],
    [1023, 1023, 1023, 1023, 1023, 1023, 511, 511, 511, 511],
    [1023, 1023, 1023, 1023, 1023, 1023, 1023, 255, 255, 255],
];

export const PAIRS_BY_PRIORITY_PREFER_POWER: Array<[number, number, number]> = ODD_TARGETS.flatMap(
    (p) => ODD_TARGETS.map((s) => [p + s, p, s] as [number, number, number]),
).sort((a, b) => b[0] - a[0] || b[1] - a[1] || b[2] - a[2]);

export const PAIRS_BY_PRIORITY_PREFER_STAMINA: Array<[number, number, number]> =
    ODD_TARGETS.flatMap((p) =>
        ODD_TARGETS.map((s) => [p + s, p, s] as [number, number, number]),
    ).sort((a, b) => b[0] - a[0] || b[2] - a[2] || b[1] - a[1]);

export type PokeathlonStats = {
    id: number;
    dex_id: string;
    name: string;
    speed: number;
    speedMax: number;
    speedMin: number;
    power: number;
    powerMax: number;
    powerMin: number;
    skill: number;
    skillMax: number;
    skillMin: number;
    stamina: number;
    staminaMax: number;
    staminaMin: number;
    jump: number;
    jumpMax: number;
    jumpMin: number;
    total: number;
};

export type SeedSearchResult = {
    offset: number;
    x_mask: number;
    num_offsets: number;
    streak: number;
    count: number;
    pid: number;
    seed: number;
};

export type Solution = {
    nature: Nature;
    flavors: IntTuple;
    recipe_effect: IntTuple;
    nature_effect: IntTuple;
    required_daily: IntTuple;
    mildness: number;
};

export type Result = {
    sol: Solution;
    recipe: string[];
    grouped: Array<[string, number]>;
    source: string;
    ingredients: number;
    daily_sum: number;
    final_mods: number[];
    seed_result: SeedSearchResult | null;
};

export function seedXValues(xMask: number): number[] {
    const out: number[] = [];
    for (let x = 1; x <= 31; x += 1) {
        if ((xMask >> x) & 1) out.push(x);
    }
    return out;
}

export function naturalCatchProbability(numOffsets: number): number {
    return (numOffsets * 42950.0) / 0xffffffff;
}
