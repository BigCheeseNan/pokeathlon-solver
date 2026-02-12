import { INGREDIENTS } from "../constants";
import type { WasmModule } from "./seed";

export type RecipeWasmExports = {
    astarMinimalRecipe: (
        target: number[],
        opts?: { quiet?: boolean; prune_relevant?: boolean },
    ) => { recipe: string[] | null; err: number };
};

export function createRecipeBindings(module: WasmModule): RecipeWasmExports {
    const writeI32 = (ptr: number, value: number) => module.setValue(ptr, value | 0, "i32");
    const readI32 = (ptr: number) => module.getValue(ptr, "i32");

    return {
        astarMinimalRecipe: (target, opts) => {
            if (target.length !== 5) {
                throw new Error("target must have length 5");
            }

            const maxSteps = 128;
            const targetPtr = module._malloc(5 * 4);
            const stepsPtr = module._malloc(maxSteps * 4);
            try {
                const targetInts = target.map((v) => Math.trunc(v));
                for (let i = 0; i < 5; i += 1) {
                    writeI32(targetPtr + i * 4, targetInts[i]);
                }

                if (typeof module.ccall === "function") {
                    if (opts?.prune_relevant !== undefined) {
                        module.ccall(
                            "recipe_calc_set_relevant_pruning",
                            "void",
                            ["number"],
                            [opts.prune_relevant ? 1 : 0],
                        );
                    }
                    if (opts?.quiet !== undefined) {
                        module.ccall(
                            "recipe_calc_set_verbose",
                            "void",
                            ["number"],
                            [opts.quiet ? 0 : 1],
                        );
                    }
                }

                const n = module.ccall(
                    "astar_minimal_recipe_c",
                    "number",
                    ["number", "number", "number"],
                    [targetPtr, stepsPtr, maxSteps],
                );

                if (n < 0) {
                    throw new Error(
                        `astar_minimal_recipe_c failed (err=${n}) target=${targetInts.join(",")}`,
                    );
                }

                const seq: string[] = [];
                for (let i = 0; i < n; i += 1) {
                    const ingIdx = readI32(stepsPtr + i * 4);
                    seq.push(INGREDIENTS[ingIdx] ?? "unknown");
                }
                return { recipe: seq, err: 0 };
            } finally {
                module._free(targetPtr);
                module._free(stepsPtr);
            }
        },
    };
}
