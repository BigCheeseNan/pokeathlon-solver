import type { FullPokemon } from "../../utils/pokemon";
import { dex3 } from "../../utils/pokemon";

type Props = {
    pokemonInput: string;
    pokemonQuery: string;
    pokemonOptions: FullPokemon[];
    selectedPokemon: FullPokemon | null;
    onInputChange: (value: string) => void;
};

function PokemonPicker({
    pokemonInput,
    pokemonQuery,
    pokemonOptions,
    selectedPokemon,
    onInputChange,
}: Props) {
    return (
        <>
            <div className="row">
                <label className="label">Pokemon</label>
                <input
                    type="text"
                    className="poke-picker"
                    list={pokemonQuery ? "pokemonFullList" : undefined}
                    placeholder="Start typing a name (e.g. Bulbasaur) or dex id (e.g. 1)"
                    value={pokemonInput}
                    onChange={(e) => onInputChange(e.target.value)}
                />
                {pokemonQuery ? (
                    <datalist id="pokemonFullList">
                        {pokemonOptions.map((p, idx) => (
                            <option
                                key={`${p.id}-${p.dex_id}-${p.name}-${idx}`}
                                value={`${p.name} (#${dex3(p.dex_id)})`}
                            />
                        ))}
                    </datalist>
                ) : null}
            </div>

            {selectedPokemon ? (
                <div className="row">
                    <img
                        className="sprite"
                        src={`/sprites/${selectedPokemon.dex_id}.png`}
                        alt={selectedPokemon.name}
                        onError={(e) => {
                            (
                                e.currentTarget as HTMLImageElement
                            ).style.display = "none";
                        }}
                    />
                    <div className="muted">
                        Base stats: {selectedPokemon.name} (#
                        {dex3(selectedPokemon.dex_id)})
                    </div>
                </div>
            ) : (
                <div className="muted">
                    Pick a Pokemon to compute for.
                </div>
            )}
        </>
    );
}

export default PokemonPicker;
