#include "hgss_searcher.h"

#include "mt_tool.h"
#include "pid_tool.h"

#include <stdio.h>
#include <stdint.h>


static void printInstructions() {
	printf("Manip instructions:\n");
	printf(" - Hit the initial seed using any Gen 4 RNG reporter\n");
	printf(" - Verify the seed using any number of Elm/Irwin calls\n");
	printf(" - Bike around until an egg is generated\n");
}

static int hgssPidSearchForOffsetNoAdvInternal(
	uint32_t target_offset,
	uint32_t* out_pid,
	uint32_t* out_seed,
	int quiet
) {
	if (!quiet) {
		printf(
			"Searching for first seed producing a PID with offset %05u (pid %% 100000)...\n\n",
			target_offset % 100000u
		);
		fflush(stdout);
	}

	const int frame = 0;
	target_offset = target_offset % 100000u;

	uint32_t delay_steps[4] = { 600, 7000, 12000, 24000 };

	uint32_t* mt = mtGetBuf();
	for (uint32_t vsync_year = delay_steps[0]; vsync_year < delay_steps[3]; vsync_year++) {
		for (uint32_t hour = 0x00000000; hour < (24 * 0x00010000); hour += 0x00010000) {
			uint32_t month_day_minute_second = 0x00000000;
			do {
				uint32_t seed = month_day_minute_second + hour + vsync_year;
				mtSrand(seed);

				uint32_t pid = pidFromMtState(mt[frame]);
				if (pid == 0x00000000) {
					continue;
				}
				if ((pid % 100000u) == target_offset) {
					if (!quiet) {
						printf("Found match!\n");
						printf("Initial seed:      %08x\n", seed);
						printf("PID:              %08x\n", pid);
						printf("\n");
						printInstructions();
					}
					if (out_pid) *out_pid = pid;
					if (out_seed) *out_seed = seed;
					return 0;
				}
			} while ((month_day_minute_second += 0x01000000) != 0x00000000);
		}
	}

	if (!quiet) {
		printf("COULD NOT FIND A SEED FOR THAT OFFSET IN THE GIVEN RANGE!\n\n");
	}
	return 1;
}

int hgssPidSearchForOffsetNoAdvRange(
	uint32_t target_offset,
	uint32_t* out_pid,
	uint32_t* out_seed
) {
	return hgssPidSearchForOffsetNoAdvInternal(target_offset, out_pid, out_seed, 0);
}

int pokeathlonFindBestSeedForCriteria(
	const int target_bonuses[5],
	uint32_t allowed_mod_mask,
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
	uint32_t best_offset = 0;
	uint32_t best_x_mask = 0;
	uint32_t num_offsets = 0;
	int best_streak = 0;
	int best_count = 0;

	int rc_best = pidFindBestOffsetForCriteria(
		target_bonuses,
		allowed_mod_mask,
		allowed_x_mask,
		&best_offset,
		&best_x_mask,
		&num_offsets,
		&best_streak,
		&best_count
	);
	if (rc_best != 0) {
		if (out_offset) *out_offset = 0;
		if (out_x_mask) *out_x_mask = 0;
		if (out_num_offsets) *out_num_offsets = 0;
		if (out_best_streak) *out_best_streak = 0;
		if (out_best_count) *out_best_count = 0;
		if (out_pid) *out_pid = 0;
		if (out_seed) *out_seed = 0;
		return 1;
	}

	if (out_offset) *out_offset = best_offset;
	if (out_x_mask) *out_x_mask = best_x_mask;
	if (out_num_offsets) *out_num_offsets = num_offsets;
	if (out_best_streak) *out_best_streak = best_streak;
	if (out_best_count) *out_best_count = best_count;

	uint32_t found_pid = 0;
	uint32_t found_seed = 0;
	int rc_seed = hgssPidSearchForOffsetNoAdvInternal(best_offset, &found_pid, &found_seed, quiet);
	if (rc_seed != 0) {
		if (out_pid) *out_pid = 0;
		if (out_seed) *out_seed = 0;
		return 2;
	}

	if (out_pid) *out_pid = found_pid;
	if (out_seed) *out_seed = found_seed;
	return 0;
}
