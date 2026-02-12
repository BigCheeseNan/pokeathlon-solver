import type { SolverDeps } from "../api";
import type { WasmModule } from "./seed";
import { createRecipeBindings } from "./recipe";
import { createSeedBindings } from "./seed";

export type WasmSolverConfig = {
    recipeJsUrl?: string;
    seedJsUrl?: string;
};

type EmscriptenFactory = (opts: {
    locateFile: (path: string) => string;
}) => Promise<WasmModule> | WasmModule;

async function loadEmscriptenModule(jsUrl: string): Promise<WasmModule> {
    const loadFromUrl = async (url: string, baseUrl?: string): Promise<WasmModule> => {
        const mod = (await import(/* @vite-ignore */ url)) as {
            default: EmscriptenFactory | WasmModule;
        };

        const locateFile = (path: string) => new URL(path, baseUrl ?? url).toString();

        let instance: unknown = mod.default;
        if (typeof instance === "function") {
            instance = (instance as EmscriptenFactory)({ locateFile });
        }

        if (instance && typeof (instance as Promise<unknown>).then === "function") {
            instance = await (instance as Promise<unknown>);
        }

        if (instance && (instance as { ready?: Promise<unknown> }).ready) {
            await (instance as { ready: Promise<unknown> }).ready;
        }

        const wasm = instance as WasmModule;
        if (!wasm.getValue) {
            throw new Error("WASM module not initialized (memory access missing)");
        }
        return wasm;
    };

    // Vite forbids importing from /public directly; use fetch+blob for public URLs.
    if (jsUrl.startsWith("/")) {
        const absoluteUrl = new URL(jsUrl, window.location.href).toString();
        const code = await fetch(absoluteUrl).then((r) => {
            if (!r.ok) throw new Error(`Failed to load WASM JS: ${r.status} ${r.statusText}`);
            return r.text();
        });
        const blobUrl = URL.createObjectURL(new Blob([code], { type: "text/javascript" }));
        try {
            return await loadFromUrl(blobUrl, absoluteUrl);
        } finally {
            URL.revokeObjectURL(blobUrl);
        }
    }

    return loadFromUrl(jsUrl);
}

export async function createWasmSolverDeps(config?: WasmSolverConfig): Promise<SolverDeps> {
    const baseUrl = new URL(import.meta.env.BASE_URL, window.location.href);
    const recipeJsUrl =
        config?.recipeJsUrl ?? new URL("wasm/librecipe_calc.js", baseUrl).toString();
    const seedJsUrl = config?.seedJsUrl ?? new URL("wasm/libhgss_seedlib.js", baseUrl).toString();

    const [recipeModule, seedModule] = await Promise.all([
        loadEmscriptenModule(recipeJsUrl),
        loadEmscriptenModule(seedJsUrl),
    ]);

    const recipeBindings = createRecipeBindings(recipeModule);
    const seedBindings = createSeedBindings(seedModule);

    return {
        recipe: async (flavors, opts) => {
            try {
                const res = recipeBindings.astarMinimalRecipe(flavors, opts);
                return {
                    recipe: res.recipe,
                    source: "wasm",
                };
            } catch (err) {
                console.error("WASM recipe solver failed", err);
                return { recipe: null, source: "wasm" };
            }
        },
        seed: async (requiredDaily, allowedModMask, allowedXValues, opts) => {
            try {
                return seedBindings.findBestSeedForCriteria(
                    requiredDaily,
                    allowedModMask,
                    allowedXValues,
                    opts,
                );
            } catch {
                return null;
            }
        },
    };
}
