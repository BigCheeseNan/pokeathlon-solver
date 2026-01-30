#include "pid_tool.h"
#include "mt_tool.h"

static uint32_t arng(uint32_t x) {
	// Forward mapping that arngInv() reverses.
	// x' = x * 0x6C078965 + 1  (mod 2^32)
	return (x * 1812433253u) + 1u;
}

static uint32_t arngInv(uint32_t x) {
	return (x * 2520285293) + 1774682003;
}

uint32_t pidPrepare(uint32_t pid) {
	uint32_t target_mtout = pid;
	
	target_mtout = mtUntemper(target_mtout);
	
	return target_mtout;
}

uint32_t pidFromMtState(uint32_t mt_state) {
	uint32_t pid = mtTemper(mt_state);
	return pid;
}

static int bonus_stat(int x, int y, int z) {
	// ((x**2 - y**2 + 4*y + z + 1) % 10) * 2 - 9
	int expr = (x * x) - (y * y) + (4 * y) + z + 1;
	return ((expr % 10) * 2) - 9;
}

static int popcount_xmask(uint32_t x_mask) {
	int c = 0;
	for (int x = 1; x <= 31; x++) {
		if (x_mask & (1u << x)) c++;
	}
	return c;
}

static int longest_consecutive_streak(uint32_t x_mask) {
	int best = 0;
	int cur = 0;
	for (int x = 1; x <= 31; x++) {
		if (x_mask & (1u << x)) {
			cur++;
			if (cur > best) best = cur;
		} else {
			cur = 0;
		}
	}
	return best;
}

static int pid_allowed_mod_pokeathlon(uint32_t pid) {
	// Legacy allow-list used by older experiments.
	// (Prefer pidMatchesPokeathlonCriteria() when wiring with external scripts.)
	switch (pid % 25u) {
		case 10u:
		case 13u:
		case 14u:
			return 1;
		default:
			return 0;
	}
}

static int pid_allowed_mod_mask(uint32_t pid, uint32_t allowed_mod_mask) {
	if (allowed_mod_mask == 0) {
		// If caller doesn't specify, treat as allow-none.
		return 0;
	}
	uint32_t idx = pid % 25u;
	return (allowed_mod_mask & (1u << idx)) != 0;
}

int pidMatchesPokeathlonCriteria(
    uint32_t pid,
    const int target_bonuses[5],
    uint32_t allowed_mod_mask,
    uint32_t* out_x_mask
) {
    if (!pid_allowed_mod_mask(pid, allowed_mod_mask)) {
        if (out_x_mask) *out_x_mask = 0;
        return 0;
    }

	uint32_t num = pid % 100000u;
	int digits[5];
	for (int i = 4; i >= 0; i--) {
		digits[i] = (int)(num % 10u);
		num /= 10u;
	}

	uint32_t mask = 0;
	for (int x = 1; x <= 31; x++) {
		int ok = 1;
		for (int y = 0; y < 5; y++) {
			int z = digits[y];
			if (bonus_stat(x, y, z) < target_bonuses[y]) {
				ok = 0;
				break;
			}
		}
		if (ok) {
			mask |= (1u << x);
		}
	}

	if (out_x_mask) {
		*out_x_mask = mask;
	}
	return mask != 0;
}

uint32_t pidXMaskForOffset(uint32_t offset, const int target_bonuses[5]) {
	// offset is a 5-digit number, but we accept any 0..99999 and extract digits.
	uint32_t num = offset % 100000u;
	int digits[5];
	for (int i = 4; i >= 0; i--) {
		digits[i] = (int)(num % 10u);
		num /= 10u;
	}

	uint32_t mask = 0;
	for (int x = 1; x <= 31; x++) {
		int ok = 1;
		for (int y = 0; y < 5; y++) {
			int z = digits[y];
			if (bonus_stat(x, y, z) < target_bonuses[y]) {
				ok = 0;
				break;
			}
		}
		if (ok) {
			mask |= (1u << x);
		}
	}
	return mask;
}

int pidFindBestOffsetForCriteria(
	const int target_bonuses[5],
	uint32_t allowed_mod_mask,
	uint32_t allowed_x_mask,
	uint32_t* out_offset,
	uint32_t* out_x_mask,
	uint32_t* out_num_offsets,
	int* out_best_streak,
	int* out_best_count
) {
	uint32_t best_offset = 0;
	uint32_t best_x_mask = 0;
	int best_streak = -1;
	int best_count = -1;
	uint32_t num_offsets = 0;

	for (uint32_t offset = 0; offset < 100000u; offset++) {
		uint32_t mod = offset % 25u;
		if ((allowed_mod_mask & (1u << mod)) == 0) {
			continue;
		}
		uint32_t x_mask = pidXMaskForOffset(offset, target_bonuses);
		if (x_mask == 0) {
			continue;
		}
		// Filter by allowed_x_mask if specified
		if (allowed_x_mask != 0) {
			if ((x_mask & allowed_x_mask) != allowed_x_mask) {
                continue;
            }
		}
		num_offsets++;
		int streak = longest_consecutive_streak(x_mask);
		int count = popcount_xmask(x_mask);
		int better = 0;
		if (best_streak < 0) {
			better = 1;
		} else if (streak != best_streak) {
			better = streak > best_streak;
		} else if (count != best_count) {
			better = count > best_count;
		} else {
			better = offset < best_offset;
		}
		if (better) {
			best_streak = streak;
			best_count = count;
			best_offset = offset;
			best_x_mask = x_mask;
		}
	}

	if (best_streak < 0) {
		if (out_offset) *out_offset = 0;
		if (out_x_mask) *out_x_mask = 0;
		if (out_num_offsets) *out_num_offsets = 0;
		if (out_best_streak) *out_best_streak = 0;
		if (out_best_count) *out_best_count = 0;
		return 1;
	}

	if (out_offset) *out_offset = best_offset;
	if (out_x_mask) *out_x_mask = best_x_mask;
	if (out_num_offsets) *out_num_offsets = num_offsets;
	if (out_best_streak) *out_best_streak = best_streak;
	if (out_best_count) *out_best_count = best_count;
	return 0;
}
