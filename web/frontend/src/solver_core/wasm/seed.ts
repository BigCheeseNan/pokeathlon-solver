import type { SeedSearchResult } from "../constants";

export type WasmModule = {
    ccall: (
        ident: string,
        returnType: "number" | "void",
        argTypes: Array<"number">,
        args: number[],
    ) => number;
    _malloc: (size: number) => number;
    _free: (ptr: number) => void;
    getValue: (ptr: number, type: "i32" | "u32") => number;
    setValue: (ptr: number, value: number, type: "i32" | "u32") => void;
};

export type SeedWasmExports = {
    findBestSeedForCriteria: (
        requiredDailyStatFlavor: number[],
        allowedModMask: number,
        allowedXValues?: number[] | null,
        opts?: { quiet?: boolean },
    ) => SeedSearchResult;
};

export function createSeedBindings(module: WasmModule): SeedWasmExports {
    const writeI32 = (ptr: number, value: number) => module.setValue(ptr, value | 0, "i32");
    const readI32 = (ptr: number) => module.getValue(ptr, "i32");
    const readU32 = (ptr: number) => module.getValue(ptr, "i32") >>> 0;

    return {
        findBestSeedForCriteria: (requiredDaily, allowedModMask, allowedXValues, opts) => {
            if (requiredDaily.length !== 5) {
                throw new Error("required_daily must have length 5");
            }

            const [power, stamina, skill, jump, speed] = requiredDaily;
            const targetBonuses = [speed, jump, skill, stamina, power];

            let allowedXMask = 0;
            if (allowedXValues) {
                for (const x of allowedXValues) {
                    if (x >= 1 && x <= 31) allowedXMask |= 1 << x;
                }
            }

            const bonusesPtr = module._malloc(5 * 4);
            const outOffsetPtr = module._malloc(4);
            const outXMaskPtr = module._malloc(4);
            const outNumOffsetsPtr = module._malloc(4);
            const outStreakPtr = module._malloc(4);
            const outCountPtr = module._malloc(4);
            const outPidPtr = module._malloc(4);
            const outSeedPtr = module._malloc(4);

            try {
                for (let i = 0; i < 5; i += 1) {
                    writeI32(bonusesPtr + i * 4, targetBonuses[i]);
                }

                const rc = module.ccall(
                    "pokeathlonFindBestSeedForCriteria",
                    "number",
                    [
                        "number",
                        "number",
                        "number",
                        "number",
                        "number",
                        "number",
                        "number",
                        "number",
                        "number",
                        "number",
                        "number",
                    ],
                    [
                        bonusesPtr,
                        allowedModMask >>> 0,
                        allowedXMask >>> 0,
                        outOffsetPtr,
                        outXMaskPtr,
                        outNumOffsetsPtr,
                        outStreakPtr,
                        outCountPtr,
                        outPidPtr,
                        outSeedPtr,
                        opts?.quiet ? 1 : 0,
                    ],
                );

                if (rc === 1) throw new Error("No valid 5-digit offsets for this criteria");
                if (rc === 2) throw new Error("Could not find a seed for the best offset");
                if (rc !== 0) throw new Error(`Unexpected C return code: ${rc}`);

                return {
                    offset: readU32(outOffsetPtr),
                    x_mask: readU32(outXMaskPtr),
                    num_offsets: readU32(outNumOffsetsPtr),
                    streak: readI32(outStreakPtr),
                    count: readI32(outCountPtr),
                    pid: readU32(outPidPtr),
                    seed: readU32(outSeedPtr),
                };
            } finally {
                module._free(bonusesPtr);
                module._free(outOffsetPtr);
                module._free(outXMaskPtr);
                module._free(outNumOffsetsPtr);
                module._free(outStreakPtr);
                module._free(outCountPtr);
                module._free(outPidPtr);
                module._free(outSeedPtr);
            }
        },
    };
}
