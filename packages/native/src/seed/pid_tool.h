#ifndef PID_TOOL_H
#define PID_TOOL_H

#include <stdint.h>

// Find the best 5-digit offsets under the given criteria, without searching for a seed.
//
// allowed_mod: required nature
// allowed_x_mask: bit i set means allow day i (1..31). If 0, all days allowed.
// Ranking:
// 1) maximize longest consecutive streak of valid x days
// 2) tie-break on number of valid days
// Ties are returned in ascending offset order.
//
// Returns 0 on success, 1 if no offset matches.
// out_offsets/out_x_masks are arrays of length 4000 to receive
// the tied best offsets and their X masks (written in ascending offset order).
// out_num_best_offsets returns the total number of tied best offsets.
//
// Returns 0 on success, 1 if no offset matches.
int pidFindBestOffsetForCriteria(
	const int target_bonuses[5],
	uint32_t allowed_mod,
	uint32_t allowed_x_mask,
	uint32_t* out_offsets,
	uint32_t* out_x_masks,
	uint32_t* out_num_offsets,
	uint32_t* out_num_best_offsets,
	int* out_best_streak,
	int* out_best_count
);

#endif
