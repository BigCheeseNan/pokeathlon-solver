import type { PokemonCandidate } from "../../types";

type Props = {
    candidates: PokemonCandidate[];
    selectedPokemon: PokemonCandidate | null;
    onSelect: (p: PokemonCandidate) => void;
};

function CandidateList({ candidates, selectedPokemon, onSelect }: Props) {
    return (
        <div className="candidateGrid">
            {candidates.map((p) => (
                <button
                    key={p.id}
                    type="button"
                    className={
                        selectedPokemon?.id === p.id
                            ? "candidate active"
                            : "candidate"
                    }
                    onClick={() => onSelect(p)}
                >
                    <img
                        className="sprite"
                        src={`/sprites/${p.dex_id}.png`}
                        alt={p.name}
                        onError={(e) => {
                            (
                                e.currentTarget as HTMLImageElement
                            ).style.display = "none";
                        }}
                    />
                    <div className="candName">{p.name}</div>
                    <div className="candMeta">bonus points: {25 - p.total}</div>
                </button>
            ))}
        </div>
    );
}

export default CandidateList;
