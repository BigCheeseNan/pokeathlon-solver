import pokeathlonStatsFull from "../../data/pokeathlon_stats_full.json";
import type { PokeathlonStats } from "../constants";

export function loadPokemonData(dataFile?: PokeathlonStats[]): PokeathlonStats[] {
    if (dataFile && dataFile.length > 0) return dataFile;
    return pokeathlonStatsFull as PokeathlonStats[];
}

export function canMeetMinStats(stats: number[], statMax: number[], minStats: number[]): boolean {
    let positiveCount = 0;
    let totalNeeded = 0;
    let maxNeeded = 0;
    let count4 = 0;

    for (let i = 0; i < 5; i++) {
        if (statMax[i] < minStats[i]) return false;

        const needed = minStats[i] - stats[i];
        if (needed > 0) {
            positiveCount++;
            totalNeeded += needed;
            maxNeeded = Math.max(maxNeeded, needed);

            if (needed === 4 && ++count4 > 1) return false;
            if (positiveCount > 3 || totalNeeded > 8) return false;
        }
    }

    if (maxNeeded === 4 && positiveCount > 2) return false;

    return true;
}

export function findLowestTotalPokemon(
    minStats: number[],
    pokemonData?: PokeathlonStats[],
    topN = 10,
): PokeathlonStats[] {
    const data = pokemonData ?? loadPokemonData();

    const filtered: PokeathlonStats[] = [];
    for (const poke of data) {
        const stats: number[] = [poke.speed, poke.power, poke.skill, poke.stamina, poke.jump];
        const statMax: number[] = [
            poke.speedMax,
            poke.powerMax,
            poke.skillMax,
            poke.staminaMax,
            poke.jumpMax,
        ];
        if (canMeetMinStats(stats, statMax, minStats)) filtered.push(poke);
    }

    filtered.sort((a, b) => a.total - b.total);
    return filtered.slice(0, topN);
}
