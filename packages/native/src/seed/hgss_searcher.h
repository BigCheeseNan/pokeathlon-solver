#ifndef HGSS_SEARCHER_H
#define HGSS_SEARCHER_H

#include <stdint.h>

#ifdef _WIN32
#define SEEDLIB_API __declspec(dllexport)
#else
#define SEEDLIB_API
#endif

// Library API: find the best PID candidates (by longest consecutive valid-day streak,
// then total valid days) and then find the first seed producing any tied-best offset.
//
// target_bonuses order is: speed, jump, skill, stamina, power.
// allowed_mod: allowed pid % 25 value.
// allowed_x_mask: bit i set means allow day i (1..31). If 0, all days allowed.
//
// Returns:
//  0: success
//  1: no valid 5-digit offsets for the criteria
//  2: could not find a seed for any tied-best offset
SEEDLIB_API int pokeathlonFindBestSeedForCriteria(
	const int target_bonuses[5],
	uint32_t allowed_mod,
	uint32_t allowed_x_mask,
	uint32_t* out_offset,
	uint32_t* out_x_mask,
	uint32_t* out_num_offsets,
	int* out_best_streak,
	int* out_best_count,
	uint32_t* out_pid,
	uint32_t* out_seed,
	int quiet
);

#endif
