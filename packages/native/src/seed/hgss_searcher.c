#include "hgss_searcher.h"
#include "pid_tool.h"

#include <stdio.h>
#include <stdint.h>
	
#define M  397

#define UPPER_MASK  0x80000000
#define LOWER_MASK  0x7FFFFFFF

#define MAX_BEST_OFFSETS 4000u

static uint32_t mag01[2] = { 0, 0x9908B0DF };

static const uint32_t delay_steps[4] = { 600u, 7000u, 12000u, 24000u };

static inline uint32_t mtTemper(uint32_t y) {
	y ^= (y >> 11);
	y ^= (y <<  7) & 0x9D2C5680;
	y ^= (y << 15) & 0xEFC60000;
	y ^= (y >> 18);
	return y;
}

static inline uint32_t mtSeedToState0(uint32_t seed) {
	uint32_t mt0 = seed;
	uint32_t mt1 = (0x6C078965u * (mt0 ^ (mt0 >> 30)) + 1u);
	uint32_t prev = mt1;
	uint32_t mtM = 0;
	for (uint32_t i = 2; i <= (uint32_t)M; i++) {
		uint32_t cur = (0x6C078965u * (prev ^ (prev >> 30)) + i);
		if (i == (uint32_t)M) {
			mtM = cur;
		}
		prev = cur;
	}

	uint32_t y = (mt0 & UPPER_MASK) | (mt1 & LOWER_MASK);
	mt0 = mtM ^ (y >> 1) ^ mag01[y & 1u];
	return mt0;
}

static int hgssPidSearchForOffsetNoAdvInternal(
	const uint32_t* target_offsets,
	const uint32_t* target_x_masks,
	uint32_t num_target_offsets,
	uint32_t* out_offset,
	uint32_t* out_x_mask,
	uint32_t* out_pid,
	uint32_t* out_seed,
	int quiet
) {
	if (!quiet) {
		printf("Searching for first seed producing a PID with a tied-best offset (pid %% 100000)...\n\n");
		fflush(stdout);
	}

	for (uint32_t vsync_year = delay_steps[0]; vsync_year < delay_steps[3]; vsync_year++) {
		for (uint32_t hour = 0; hour < 24; hour++) {
            for (uint32_t month_day_min_sec = 0; month_day_min_sec < 0x100 ; month_day_min_sec ++) {
				uint32_t seed = (month_day_min_sec << 24) + (hour << 16) + vsync_year;
				uint32_t pid = mtTemper(mtSeedToState0(seed));
				if (pid == 0) continue;

				uint32_t pid_offset = pid % 100000;
				for (uint32_t i = 0; i < num_target_offsets; i++) {
					if (pid_offset != (target_offsets[i])) continue;

					if (!quiet) {
						printf("Found match!\nInitial seed: %08x\nPID: %08x\nVsync year: %u\n\n",
								seed, pid, vsync_year);
					}
					*out_offset = target_offsets[i];
					*out_x_mask = target_x_masks ? target_x_masks[i] : 0;
					*out_pid = pid;
					*out_seed = seed;
					return 0;
				}
			}
		}
	}

	if (!quiet) {
		printf("COULD NOT FIND A SEED FOR THAT OFFSET IN THE GIVEN RANGE!\n\n");
	}
	return 1;
}

int pokeathlonFindBestSeedForCriteria(
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
) {
	uint32_t best_offsets[MAX_BEST_OFFSETS];
	uint32_t best_x_masks[MAX_BEST_OFFSETS];
	uint32_t num_offsets = 0;
	uint32_t num_best_offsets = 0;
	int best_streak = 0;
	int best_count = 0;

	int rc_best = pidFindBestOffsetForCriteria(
		target_bonuses,
		allowed_mod,
		allowed_x_mask,
		best_offsets,
		best_x_masks,
		&num_offsets,
		&num_best_offsets,
		&best_streak,
		&best_count
	);
	if (rc_best != 0) {
		*out_num_offsets = 0;
		*out_best_streak = 0;
		*out_best_count = 0;
		*out_pid = 0;
		*out_seed = 0;
		return 1;
	}

	*out_offset = best_offsets[0];
	*out_x_mask = best_x_masks[0];
	*out_num_offsets = num_offsets;
	*out_best_streak = best_streak;
	*out_best_count = best_count;

	int rc_seed = hgssPidSearchForOffsetNoAdvInternal(
		best_offsets,
		best_x_masks,
		num_best_offsets,
		out_offset,
		out_x_mask,
		out_pid,
		out_seed,
		quiet
	);
	if (rc_seed != 0) {
		*out_pid = 0;
		*out_seed = 0;
		return 2;
	}

	return 0;
}
