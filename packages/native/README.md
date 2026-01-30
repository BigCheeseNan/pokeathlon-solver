# Pokeathlon Native Libraries

High-performance C implementations for Pokeathlon solver computations.

## Overview

This package contains optimized C code for computationally intensive parts of the Pokeathlon solver:

1. **recipe_calc** - A* recipe solver for finding minimal Aprijuice ingredient sequences
2. **hgss_seedlib** - PID/seed search for Pokemon HeartGold/SoulSilver RNG

These libraries are automatically loaded by `solver-core` when available, providing 10-50x speedup over pure Python implementations.

## Building

### Prerequisites

- **Windows**: MinGW-w64 or Visual Studio 2019+
- **Linux/macOS**: GCC or Clang
- **CMake**: 3.15 or higher

### Build Commands

```bash
# Configure (one-time setup)
cmake -B build -G "MinGW Makefiles"          # Windows (MinGW)
# Or: cmake -B build -G "Visual Studio 17 2022"  # Windows (MSVC)
# Or: cmake -B build -G "Ninja"                   # Cross-platform

# Build both libraries
cmake --build build --config Release

# Clean build
cmake --build build --target clean
cmake --build build --config Release
```

The build automatically copies the compiled libraries to `../solver_core/src/solver_core/bindings/`.

### Build Outputs

- **Windows**: `recipe_calc.dll`, `hgss_seedlib.dll`
- **Linux**: `librecipe_calc.so`, `libhgss_seedlib.so`
- **macOS**: `librecipe_calc.dylib`, `libhgss_seedlib.dylib`

## Libraries

### recipe_calc

**Purpose**: Fast A* search for minimal ingredient recipes to reach flavor targets.

**Source**: `src/recipe/recipe_calculator.c`

**API**:
```c
int astar_minimal_recipe_c(
    int target[5],        // Target flavors (power, stamina, skill, jump, speed)
    int steps_out[512],   // Output: ingredient sequence (as indices 0-6)
    int max_steps         // Maximum steps to consider
);
```

**Returns**: Number of steps (ingredients) in recipe, or negative on failure.

**Python Binding**: Automatically loaded by `solver_core.bindings.c_recipe_wrapper`

### hgss_seedlib

**Purpose**: Search for Pokemon PIDs and initial seeds that satisfy daily modifier requirements.

**Sources**:
- `src/seed/hgss_searcher.c` - Main search algorithm
- `src/seed/mt_tool.c` - Mersenne Twister RNG
- `src/seed/pid_tool.c` - PID generation utilities

**API**:
```c
int pokeathlonFindBestSeedForCriteria(
    int required_daily[5],      // Required daily bonuses (C order: speed,jump,skill,stamina,power)
    uint32_t allowed_mods,      // Bitmask of allowed nature modifiers
	uint32_t allowed_x_mask,    // Bitmask of required days
    uint32_t* out_offset,       // Output: best offset pattern
    uint32_t* out_x_mask,       // Output: valid X days (bitmask)
    uint32_t* out_num_offsets,  // Output: number of valid offsets
    int* out_streak,            // Output: maximum consecutive days
    int* out_count,             // Output: total valid days
    uint32_t* out_pid,          // Output: found PID
    uint32_t* out_seed,         // Output: initial seed
    int quiet                   // Suppress debug output
);
```

**Returns**: 0 on success, 1 if no valid offsets, 2 if seed search failed.

**Python Binding**: Automatically loaded by `solver_core.bindings.hgss_seedlib_wrapper`

## Project Structure

```
native/
├── CMakeLists.txt              # Build configuration
├── build/                      # Build artifacts (gitignored)
├── src/
│   ├── recipe/
│   │   └── recipe_calculator.c # A* recipe solver
│   └── seed/
│       ├── hgss_searcher.c     # Main PID/seed search
│       ├── mt_tool.c           # Mersenne Twister RNG
│       ├── pid_tool.c          # PID utilities
└── README.md
```

## Optimization Flags

CMake automatically applies optimizations:

- **GCC/Clang**: `-Ofast -Wall -Wextra`
- **MSVC**: `/O2 /W3`

## Development

### Adding New Functions

1. Add C function to appropriate source file
2. Update CMakeLists.txt if adding new source files
3. Create/update Python wrapper in `solver_core/src/solver_core/bindings/`
4. Rebuild: `cmake --build build --config Release`
5. Test with Python: `python -c "from solver_core.bindings import your_function"`

### Debugging

```bash
# Build with debug symbols
cmake -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build

# Run with debugger
gdb ./build/bin/your_test
```
