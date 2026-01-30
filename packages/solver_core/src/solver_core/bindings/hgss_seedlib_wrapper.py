"""ctypes wrapper around the HGSS seed-search C library.

Provides seed search functionality for HGSS Pokéathlon stat manipulation.

C API expects bonuses in order: (speed, jump, skill, stamina, power).
The rest of this repo typically uses STAT_FLAVOR order:
(power, stamina, skill, jump, speed).
"""

from __future__ import annotations
import sys
import ctypes
from pathlib import Path
from typing import Callable, Optional
from solver_core.constants import SeedSearchResult, intup

LIB_NAME = "libhgss_seedlib"


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

    # Legacy fallback: original location
    legacy_lib = repo_root / "Gen-4-Egg-PID-RNG-Tool" / "hgss_seedlib.dll"
    if legacy_lib.exists():
        return legacy_lib

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


class HGSSSeedLib:
    """Typed wrapper around the HGSS seed search C library.

    Avoids Pylance/Pyright errors about unknown dynamic attributes on ctypes.CDLL.
    Provides type-safe access to C functions.
    """

    pokeathlonFindBestSeedForCriteria: Callable[..., int]

    def __init__(self, path: Path):
        """Initialize library wrapper.
        
        Args:
            path: Path to the shared library file
        """
        raw = ctypes.CDLL(str(path))
        self._raw = raw

        # Setup pokeathlonFindBestSeedForCriteria
        func = raw.pokeathlonFindBestSeedForCriteria
        func.argtypes = [
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.c_int,
        ]
        func.restype = ctypes.c_int
        self.pokeathlonFindBestSeedForCriteria = func


# Global cached library instance
_lib_instance: Optional[HGSSSeedLib] = None


def _get_lib(lib_path: Path | None = None) -> HGSSSeedLib:
    """Get or create cached library instance."""
    global _lib_instance
    if _lib_instance is None:
        path = _load_lib(lib_path)
        _lib_instance = HGSSSeedLib(path)
    return _lib_instance


def find_best_seed_for_criteria(
    required_daily_stat_flavor: intup,
    allowed_mod_mask: int,
    allowed_x_values: list[int] | None = None,
    *,
    quiet: bool = True,
    lib_path: Path | None = None,
) -> SeedSearchResult:
    """Find best seed/PID for given Pokéathlon stat criteria.

    Input order: STAT_FLAVOR = (power, stamina, skill, jump, speed)
    
    Args:
        required_daily_stat_flavor: Minimum daily bonuses needed (STAT_FLAVOR order)
        allowed_mod_mask: Bitmask of allowed PID mod 25 values
        allowed_x_values: Optional list of allowed days (1-31). If None, all days allowed
        quiet: Suppress C library output
        lib_path: Custom library path (default searches standard locations)
        
    Returns:
        SeedSearchResult with offset, valid days, streak info, PID, and seed
        
    Raises:
        ValueError: If no valid offsets found or seed search failed
        RuntimeError: If unexpected C library error occurred
    """
    # Convert to C order: (speed, jump, skill, stamina, power)
    power, stamina, skill, jump, speed = required_daily_stat_flavor
    target_bonuses = (speed, jump, skill, stamina, power)
    
    # Convert allowed_x_values list to bitmask
    allowed_x_mask = 0
    if allowed_x_values is not None:
        for x in allowed_x_values:
            if 1 <= x <= 31:
                allowed_x_mask |= (1 << x)

    lib = _get_lib(lib_path)

    bonuses_arr = (ctypes.c_int * 5)(*target_bonuses)

    out_offset = ctypes.c_uint32(0)
    out_x_mask = ctypes.c_uint32(0)
    out_num_offsets = ctypes.c_uint32(0)
    out_streak = ctypes.c_int(0)
    out_count = ctypes.c_int(0)
    out_pid = ctypes.c_uint32(0)
    out_seed = ctypes.c_uint32(0)

    rc = lib.pokeathlonFindBestSeedForCriteria(
        bonuses_arr,
        ctypes.c_uint32(allowed_mod_mask),
        ctypes.c_uint32(allowed_x_mask),
        ctypes.byref(out_offset),
        ctypes.byref(out_x_mask),
        ctypes.byref(out_num_offsets),
        ctypes.byref(out_streak),
        ctypes.byref(out_count),
        ctypes.byref(out_pid),
        ctypes.byref(out_seed),
        ctypes.c_int(1 if quiet else 0),
    )

    if rc == 1:
        raise ValueError("No valid 5-digit offsets for this criteria")
    if rc == 2:
        raise ValueError("Could not find a seed for the best offset")
    if rc != 0:
        raise RuntimeError(f"Unexpected C return code: {rc}")

    return SeedSearchResult(
        offset=int(out_offset.value),
        x_mask=int(out_x_mask.value),
        num_offsets=int(out_num_offsets.value),
        streak=int(out_streak.value),
        count=int(out_count.value),
        pid=int(out_pid.value),
        seed=int(out_seed.value),
    )

if __name__ == "__main__":
    # Input order: (power, stamina, skill, jump, speed)
    result = find_best_seed_for_criteria(
        required_daily_stat_flavor=(5, -9, 9, -9, -7),
        allowed_mod_mask=1 << 3 | 1 << 4,  # Only mod 25 natures 3 and 4
        quiet=False,
    )
    print("Result:", result)
    print(f"Valid days: {result.x_values}")