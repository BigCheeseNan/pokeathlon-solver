"""ctypes wrapper around the recipe calculation C library.

Provides A* search for minimal Aprijuice recipes using native code.
"""

from __future__ import annotations
import os
import sys
import ctypes
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Optional
from solver_core.constants import INGREDIENTS
from solver_core.recipe import reduce_recipe

LIB_NAME = "librecipe_calc"


def _get_lib_filename() -> str:
    """Get platform-specific library filename."""
    if sys.platform.startswith("win"):
        return f"{LIB_NAME}.dll"
    elif sys.platform == "darwin":
        return f"{LIB_NAME}.dylib"
    else:
        return f"{LIB_NAME}.so"


def _default_lib_path() -> Path:
    """Get default library path with fallback locations."""
    # Primary: same directory as this file (bindings/)
    local_lib = Path(__file__).parent / _get_lib_filename()
    if local_lib.exists():
        return local_lib

    # Development fallback: check packages/native/build/bin/
    repo_root = Path(__file__).resolve().parents[4]
    dev_lib = repo_root / "packages" / "native" / "build" / "bin" / _get_lib_filename()
    if dev_lib.exists():
        return dev_lib

    # Return primary location for error message
    return local_lib


def _load_lib(lib_path: Path | None = None) -> Path:
    """Locate and validate library path."""
    lib_path = lib_path or _default_lib_path()
    if not lib_path.exists():
        raise FileNotFoundError(
            f"Shared library not found: {lib_path}. "
            f"Build it first using CMake in packages/native/"
        )
    return lib_path


class RecipeCalcLib:
    """Typed wrapper around the C shared library.

    Avoids Pylance/Pyright errors about unknown dynamic attributes on ctypes.CDLL.
    Provides type-safe access to C functions.
    """

    astar_minimal_recipe_c: Callable[
        [ctypes.Array[ctypes.c_int], ctypes.Array[ctypes.c_int], int], int
    ]
    recipe_calc_set_relevant_pruning: Callable[[int], None]
    recipe_calc_set_verbose: Optional[Callable[[int], None]]

    def __init__(self, path: Path):
        """Initialize library wrapper.

        Args:
            path: Path to the shared library file
        """
        raw = ctypes.CDLL(str(path))
        self._raw = raw

        # Setup astar_minimal_recipe_c
        astar = raw.astar_minimal_recipe_c
        astar.argtypes = [
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_int,
        ]
        astar.restype = ctypes.c_int
        self.astar_minimal_recipe_c = astar

        # Setup recipe_calc_set_relevant_pruning
        set_prune = raw.recipe_calc_set_relevant_pruning
        set_prune.argtypes = [ctypes.c_int]
        set_prune.restype = None
        self.recipe_calc_set_relevant_pruning = set_prune

        # Setup recipe_calc_set_verbose (optional - older DLLs may not export it)
        try:
            set_verbose = raw.recipe_calc_set_verbose
        except AttributeError:
            self.recipe_calc_set_verbose = None
        else:
            set_verbose.argtypes = [ctypes.c_int]
            set_verbose.restype = None
            self.recipe_calc_set_verbose = set_verbose


# Global cached library instance
_lib_instance: Optional[RecipeCalcLib] = None


def _get_lib(lib_path: Path | None = None) -> RecipeCalcLib:
    """Get or create cached library instance."""
    global _lib_instance
    if _lib_instance is None:
        path = _load_lib(lib_path)
        _lib_instance = RecipeCalcLib(path)
    return _lib_instance


@contextmanager
def _suppress_c_stdout(enabled: bool):
    """Temporarily silence C stdout (printf) when enabled."""
    if not enabled:
        yield
        return
    sys.stdout.flush()
    # On Windows, fd 1 is stdout for the C runtime as well.
    devnull_fd = os.open(os.devnull, os.O_RDWR)
    saved_fd = os.dup(1)
    try:
        os.dup2(devnull_fd, 1)
        yield
    finally:
        os.dup2(saved_fd, 1)
        os.close(saved_fd)
        os.close(devnull_fd)


def astar_minimal_recipe(
    target: tuple[int, ...],
    *,
    quiet: bool = False,
    prune_relevant: bool = True,
    lib_path: Path | None = None,
) -> tuple[Optional[list[str]], float, int]:
    """Find minimal Aprijuice recipe using A* search.

    Args:
        target: Target flavor values (length 5 tuple)
        quiet: Suppress C library output
        prune_relevant: Enable relevant-flavor pruning optimization
        lib_path: Custom library path (default searches standard locations)

    Returns:
        Tuple of (recipe_sequence, elapsed_time, error_code)
        - recipe_sequence: List of ingredient names, or None if failed
        - elapsed_time: Search duration in seconds
        - error_code: 0 on success, negative on failure
    """
    if len(target) != 5:
        raise ValueError("target must have length 5")

    lib = _get_lib(lib_path)

    target_arr = (ctypes.c_int * 5)(*target)
    max_steps = 512
    steps_out = (ctypes.c_int * max_steps)()
    lib.recipe_calc_set_relevant_pruning(int(bool(prune_relevant)))

    # Prefer C-side verbosity switch (clean + cross-platform)
    # Fall back to fd redirection when running against an older DLL
    if lib.recipe_calc_set_verbose is not None:
        lib.recipe_calc_set_verbose(0 if quiet else 1)

    start = time.time()
    with _suppress_c_stdout(quiet and lib.recipe_calc_set_verbose is None):
        n = lib.astar_minimal_recipe_c(target_arr, steps_out, max_steps)
    elapsed = time.time() - start

    if n < 0:
        return None, elapsed, n

    seq = [INGREDIENTS[steps_out[i]] for i in range(n)]
    return seq, elapsed, 0


if __name__ == "__main__":
    # power, stamina, skill, jump, speed
    targets = [
        (1, 1, 1, 38, 1),
    ]
    for target in targets:
        seq, t, err = astar_minimal_recipe(target, quiet=False, prune_relevant=True)
        if seq is None:
            print("Failed (err)", err)
        else:
            print("Time: %.3f s" % t)
            print(f"Recipe sequence: {seq}")
            for ing, cnt in reduce_recipe(seq, target):
                print(f"  {ing} x{cnt}")
            print("Total steps:", len(seq))
