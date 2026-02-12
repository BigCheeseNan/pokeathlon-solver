#include "pid_tool.h"

static inline int bonus_stat(int x, int y, int z) {
	// ((x**2 - y**2 + 4*y + z + 1) % 10) * 2 - 9
	int expr = (x * x) - (y * y) + (4 * y) + z + 1;
	return ((expr % 10) * 2) - 9;
}

static inline int popcount_xmask(uint32_t x_mask) {
	int c = 0;
	for (int x = 1; x <= 31; x++) {
		if (x_mask & (1u << x)) c++;
	}
	return c;
}

static inline int longest_consecutive_streak(uint32_t x) {
	int streak = 0;
	while (x) {
		x &= (x << 1);
		streak++;
	}
	return streak;
}

static inline uint32_t pidXMaskForOffset(uint32_t offset, const int target_bonuses[5]) {
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
	uint32_t allowed_mod,
	uint32_t allowed_x_mask,
	uint32_t* out_offsets,
	uint32_t* out_x_masks,
	uint32_t* out_num_offsets,
	uint32_t* out_num_best_offsets,
	int* out_best_streak,
	int* out_best_count
) {
	int best_streak = -1;
	int best_count = -1;
	uint32_t num_offsets = 0;
	uint32_t num_best_offsets = 0;

	for (uint32_t offset = allowed_mod; offset < 100000u; offset += 25) {
		uint32_t x_mask = pidXMaskForOffset(offset, target_bonuses);
		if (!x_mask) continue;

		if (allowed_x_mask && ((x_mask & allowed_x_mask) != allowed_x_mask)) continue;

		num_offsets++;

		int streak = longest_consecutive_streak(x_mask);
		int count = popcount_xmask(x_mask);

		int better = (best_streak < 0) ||
			(streak > best_streak) ||
			(streak == best_streak && count > best_count);

		if (better) {
			best_streak = streak;
			best_count = count;
			num_best_offsets = 1;
			out_offsets[0] = offset;
			out_x_masks[0] = x_mask;
		} else if (streak == best_streak && count == best_count) {
			out_offsets[num_best_offsets] = offset;
			out_x_masks[num_best_offsets] = x_mask;
			num_best_offsets++;
		}
	}

	if (best_streak < 0) {
		return 1;
	}

	*out_num_offsets = num_offsets;
	*out_num_best_offsets = num_best_offsets;
	*out_best_streak = best_streak;
	*out_best_count = best_count;

	return 0;
}
