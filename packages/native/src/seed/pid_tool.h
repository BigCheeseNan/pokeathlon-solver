#ifndef PID_TOOL_H
#define PID_TOOL_H

#include <stdint.h>

uint32_t pidPrepare(uint32_t pid);

// Convert an internal MT state word back into the egg PID that would be produced.
// If international is non-zero, applies the same 4-step ARNG forward mapping that
// pidPrepare() inverses.
uint32_t pidFromMtState(uint32_t mt_state);

// More general version used for wiring this tool with external scripts.
//
// target_bonuses order is: speed, jump, skill, stamina, power (y = 0..4 in bonus_stat())
// allowed_mod_mask: bit i set means allow pid % 25 == i.
//
// Returns non-zero if there exists at least one x in 1..31 meeting all constraints.
// If out_x_mask is not NULL, bits 1..31 indicate which x values satisfy bonuses.
int pidMatchesPokeathlonCriteria(
	uint32_t pid,
	const int target_bonuses[5],
	uint32_t allowed_mod_mask,
	uint32_t* out_x_mask
);

// Compute which x values (1..31) satisfy the given bonuses for a fixed 5-digit offset.
// offset must be in [0..99999].
// target_bonuses order is: speed, jump, skill, stamina, power.
// Returns a mask where bits 1..31 indicate valid x values.
uint32_t pidXMaskForOffset(uint32_t offset, const int target_bonuses[5]);

// Find the best 5-digit offset under the given criteria, without searching for a seed.
//
// allowed_mod_mask: bit i set means allow offset % 25 == i.
// allowed_x_mask: bit i set means allow day i (1..31). If 0, all days allowed.
// Ranking:
// 1) maximize longest consecutive streak of valid x days
// 2) tie-break on number of valid days
// 3) tie-break on smaller offset (stable)
//
// Returns 0 on success, 1 if no offset matches.
int pidFindBestOffsetForCriteria(
	const int target_bonuses[5],
	uint32_t allowed_mod_mask,
	uint32_t allowed_x_mask,
	uint32_t* out_offset,
	uint32_t* out_x_mask,
	uint32_t* out_num_offsets,
	int* out_best_streak,
	int* out_best_count
);

#endif
