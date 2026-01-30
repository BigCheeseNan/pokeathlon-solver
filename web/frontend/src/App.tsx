import { useEffect, useState } from "react";
import "./App.css";
import type { Mode } from "./types";
import StarSearchMode from "./components/star-search/StarSearchMode";
import PokemonSearchMode from "./components/pokemon-search/PokemonSearchMode";

function App() {
    const [mode, setMode] = useState<Mode>("pokemon");
    const [theme, setTheme] = useState<"light" | "dark">(() => {
        const stored = localStorage.getItem("theme");
        if (stored === "light" || stored === "dark") return stored;
        return window.matchMedia("(prefers-color-scheme: light)").matches
            ? "light"
            : "dark";
    });

    useEffect(() => {
        document.documentElement.setAttribute("data-theme", theme);
        localStorage.setItem("theme", theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme((prev) => (prev === "dark" ? "light" : "dark"));
    }; 

    

    return (
        <div className="page">
            <header className="header">
                <div className="headerContent">
                    <h1>Pokeathlon Solver</h1>
                    <button
                        type="button"
                        className="themeToggle"
                        onClick={toggleTheme}
                        aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
                    >
                        {theme === "dark" ? "☀️ " : "🌙 "}
                        {theme === "dark" ? "Light" : "Dark"}
                    </button>
                </div>
            </header>

            <div className="panel">
                <div className="row">
                    <label className="label">Mode</label>
                    <div className="seg">
                        <button
                            type="button"
                            className={
                                mode === "pokemon" ? "segBtn active" : "segBtn"
                            }
                            onClick={() => setMode("pokemon")}
                        >
                            Star Search
                        </button>
                        <button
                            type="button"
                            className={
                                mode === "diffs" ? "segBtn active" : "segBtn"
                            }
                            onClick={() => setMode("diffs")}
                        >
                            Pokemon Search
                        </button>
                    </div>
                </div>
            </div>

            {mode === "pokemon" ? <StarSearchMode /> : <PokemonSearchMode />}
        </div>
    );
}

export default App;
