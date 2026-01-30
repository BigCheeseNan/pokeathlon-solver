# Pokeathlon Solver Core

Core solver logic for optimizing Pokemon Pokeathlon stats through recipes, natures, and daily modifiers.

## Overview

This package finds optimal ingredient recipes and Pokemon PIDs to achieve target Pokeathlon stat bonuses in Pokemon HeartGold/SoulSilver. It combines:

- **Recipe solving**: Finding minimal Aprijuice ingredient sequences to reach flavor targets
- **Nature optimization**: Testing all 25 natures to find stat bonus combinations
- **PID/seed search**: Finding valid Pokemon IDs and initial seeds for daily modifier requirements
- **Pokemon filtering**: Identifying lowest-stat Pokemon that can meet minimum requirements

## Installation

### Development Mode (Editable)

```bash
# From repository root
cd packages/solver_core
pip install -e .
```

### Quick Start (PyPI)

```bash
pip install pokeathlon-solver-core
```

### Dependencies

- Python 3.10+
- No external Python dependencies (pure Python + optional C bindings)

### Optional: C Performance Bindings

For faster recipe solving, build the native libraries:

```bash
cd ../native
cmake -B build -G "MinGW Makefiles"  # Or your preferred generator
cmake --build build --config Release
# DLLs are automatically copied to solver_core/bindings/
```

## Usage

### As a Library

```python
from solver_core import solve_from_star_diffs, solve_from_pokemon_stars, SolveOptions

# Method 1: Direct star difference solving
# Order: (power, stamina, skill, jump, speed), each in [-4..4]
result = solve_from_star_diffs(
    desired_star_diffs=(2, 1, 0, -1, 3),
    options=SolveOptions(compute_seed=True, top_n_solutions=10)
)

# Method 2: Pokemon-based solving
# Order: (speed, power, skill, stamina, jump), each in [1..5]
result = solve_from_pokemon_stars(
    desired_stars_speed_order=(5, 3, 2, 4, 1),
    options=SolveOptions(pokemon_top_n=10)
)

# Access results
for solution in result['results']:
    print(f"Nature: {solution['nature']['name']}")
    print(f"Ingredients: {solution['ingredients']}")
    print(f"Recipe: {solution['grouped_ingredients']}")
    if solution['seed_result']:
        print(f"PID: {solution['seed_result']['pid']:08X}")
        print(f"Days: {solution['seed_result']['days']}")
```

### Command Line Interface

```bash
# Solve from star diffs (power stamina skill jump speed)
python -m solver_core.cli 2 1 0 -2 3

# Solve from desired Pokemon stars
python -m solver_core.cli 5 3 2 4 1 --mode pokemon

# List Pokemon candidates only (no recipe solving)
python -m solver_core.cli 5 3 2 4 1 --mode candidates

# Limit candidate pokemon to 3 (default 10), also works in pokemon mode
python -m solver_core.cli 5 3 2 4 1 --mode candidates --top-n 3

# Solve for easiest daily requirements and not least ingredients
python -m solver_core.cli 5 3 2 4 1 --mode pokemon --max

# Outputs all solutions for all Pokemon rather than only the best solution
python -m solver_core.cli 5 3 2 4 1 --mode pokemon --full

# Solve from desired Pokemon stars (speed order input)
python -m solver_core.cli 5 3 2 4 1 --mode pokemon --speed-order
```

## Package Structure

```
solver_core/
├── __init__.py           # Public API exports
├── api.py                # JSON-friendly API functions
├── cli.py                # Command-line interface
├── constants.py          # Shared constants, types, natures
├── main/                 # Core solver logic
│   ├── solution.py       # Nature enumeration & solution finding
│   ├── modifiers.py      # Star/nature/daily modifier calculations
│   ├── flavors.py        # Min/max flavor computation
│   └── utils.py          # Helper functions
├── recipe/               # Recipe solving
│   ├── astar_solver.py   # Pure Python A* recipe solver
│   └── reduce.py         # Recipe optimization/grouping
├── bindings/             # C library wrappers
│   ├── c_recipe_wrapper.py       # Fast C-based recipe solver
│   └── hgss_seedlib_wrapper.py   # PID/seed search library
└── poke_finder/          # Pokemon data & filtering
    ├── find_lowest_total_pokemon.py
    └── pokeathlon_stats_full.json
```

## API Reference

### Core Functions

#### `solve_from_star_diffs(desired_star_diffs, *, options=None)`

Solve for specific stat difference requirements.

**Parameters:**
- `desired_star_diffs`: Tuple of 5 integers in [-4..4], order: (power, stamina, skill, jump, speed)
- `options`: `SolveOptions` instance (optional)

**Returns:** Dict with keys:
- `results`: List of solutions, sorted by ingredient count
- `solutions_total`: Total feasible (nature, flavor) combinations
- `solutions_with_recipes`: Solutions with valid recipes
- `recipe_failures`: Count of recipe solver failures
- `invalid_seeds`: Count of solutions with no valid PID/seed

#### `solve_from_pokemon_stars(desired_stars_speed_order, *, options=None)`

Find Pokemon candidates and solve for each.

**Parameters:**
- `desired_stars_speed_order`: Tuple of 5 integers in [1..5], order: (speed, power, skill, stamina, jump)
- `options`: `SolveOptions` instance (optional)

**Returns:** Dict with keys:
- `candidates`: List of candidate Pokemon
- `cases`: List of solve results (one per Pokemon)

#### `list_pokemon_candidates(desired_stars_speed_order, *, top_n=10, data_file=None)`

List Pokemon that can meet minimum stat requirements.

**Parameters:**
- `desired_stars_speed_order`: Tuple of 5 integers in [1..5]
- `top_n`: Number of candidates to return (default: 10)
- `data_file`: Path to JSON data (optional, uses bundled data by default)

**Returns:** Dict with candidate Pokemon list

### SolveOptions

```python
@dataclass(frozen=True)
class SolveOptions:
    compute_seed: bool = True           # Find PID/seed for each solution
    top_n_solutions: int | None = None  # Limit solutions (None = all)
    pokemon_top_n: int = 10             # Pokemon candidates to consider
    pokemon_data_file: str | None = None  # Custom Pokemon data path
    search_mode: str = "min"            # "min" or "max"
    allowed_x_values: list[int] | None = None  # Allowed days (1-31) for seed search
```

## Development

### Running Tests

```bash
pytest tests/
```

### Type Checking

```bash
mypy src/solver_core/
```
