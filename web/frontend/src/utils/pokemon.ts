import pokeathlonStatsFull from "../data/pokeathlon_stats_full.json";
import type { StatKey } from "../types";
import { STAT_ORDER } from "../constants";

export type FullPokemon = {
    id: number;
    dex_id: string;
    name: string;
    powerMin: number;
    power: number;
    powerMax: number;
    staminaMin: number;
    stamina: number;
    staminaMax: number;
    skillMin: number;
    skill: number;
    skillMax: number;
    jumpMin: number;
    jump: number;
    jumpMax: number;
    speedMin: number;
    speed: number;
    speedMax: number;
    total: number;
    totalMax: number;
};

export const FULL_POKEMON = pokeathlonStatsFull as FullPokemon[];

export function reorderDiffsToStats(diffsArray: number[]): number[] {
    const map: Record<StatKey, number> = {
        power: diffsArray[0],
        stamina: diffsArray[1],
        skill: diffsArray[2],
        jump: diffsArray[3],
        speed: diffsArray[4],
    };
    return STAT_ORDER.map((k) => map[k]);
}

export function dex3(dexId: string) {
    const n = Number(dexId);
    if (Number.isFinite(n)) return String(n).padStart(3, "0");
    return dexId;
}

export function clampInt(n: number, min: number, max: number) {
    return Math.min(max, Math.max(min, Math.round(n)));
}

export function getTriplet(p: FullPokemon, stat: StatKey) {
    switch (stat) {
        case "power":
            return { min: p.powerMin, base: p.power, max: p.powerMax };
        case "stamina":
            return { min: p.staminaMin, base: p.stamina, max: p.staminaMax };
        case "skill":
            return { min: p.skillMin, base: p.skill, max: p.skillMax };
        case "jump":
            return { min: p.jumpMin, base: p.jump, max: p.jumpMax };
        case "speed":
            return { min: p.speedMin, base: p.speed, max: p.speedMax };
    }
}

export function baseStars(p: FullPokemon): Record<StatKey, number> {
    return {
        speed: p.speed,
        power: p.power,
        skill: p.skill,
        stamina: p.stamina,
        jump: p.jump,
    };
}

export function hex32(x: number) {
    const v = (x >>> 0).toString(16).padStart(8, "0");
    return `0x${v}`;
}
