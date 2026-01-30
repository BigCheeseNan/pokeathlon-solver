#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "hgss_searcher.h"
#include "pid_tool.h"

static void usage(const char* exe) {
	printf("Usage:\n");
	printf("  %s --daily P S Sk J Sp --nature-idx N \n", exe);
	printf("  %s --daily P S Sk J Sp --nature-mask HEX \n", exe);
	printf("\n");
	printf("--daily is in STAT_FLAVOR order: power stamina skill jump speed\n");
	printf("Nature index uses pid %% 25 and your Python nature ordering.\n");
}

static int parse_int(const char* s, int* out) {
	char* end = NULL;
	long v = strtol(s, &end, 10);
	if (!s[0] || (end && *end != '\0')) return 0;
	*out = (int)v;
	return 1;
}

static int parse_u32_hex(const char* s, uint32_t* out) {
	char* end = NULL;
	unsigned long v = strtoul(s, &end, 16);
	if (!s[0] || (end && *end != '\0')) return 0;
	*out = (uint32_t)v;
	return 1;
}

static void printXMask(uint32_t x_mask) {
	int first = 1;
	printf("x values: [");
	for (int x = 1; x <= 31; x++) {
		if (x_mask & (1u << x)) {
			if (!first) printf(", ");
			printf("%d", x);
			first = 0;
		}
	}
	printf("]\n");
}

int main(int argc, char** argv) {

	int have_daily = 0;
	int daily_stat_flavor[5] = { 0, 0, 0, 0, 0 }; // power stamina skill jump speed
	uint32_t allowed_mod_mask = 0;

	for (int i = 1; i < argc; i++) {
		if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
			usage(argv[0]);
			return 0;
		}
		if (strcmp(argv[i], "--daily") == 0) {
			if (i + 5 >= argc) {
				printf("ERROR: --daily expects 5 integers\n\n");
				usage(argv[0]);
				return 2;
			}
			for (int k = 0; k < 5; k++) {
				int v = 0;
				if (!parse_int(argv[i + 1 + k], &v)) {
					printf("ERROR: invalid --daily value: %s\n\n", argv[i + 1 + k]);
					return 2;
				}
				daily_stat_flavor[k] = v;
			}
			have_daily = 1;
			i += 5;
			continue;
		}
		if (strcmp(argv[i], "--nature-idx") == 0) {
			if (i + 1 >= argc) {
				printf("ERROR: --nature-idx expects an integer\n\n");
				return 2;
			}
			int idx = 0;
			if (!parse_int(argv[i + 1], &idx) || idx < 0 || idx > 24) {
				printf("ERROR: invalid nature index: %s\n\n", argv[i + 1]);
				return 2;
			}
			allowed_mod_mask |= (1u << (uint32_t)idx);
			i += 1;
			continue;
		}
		if (strcmp(argv[i], "--nature-mask") == 0) {
			if (i + 1 >= argc) {
				printf("ERROR: --nature-mask expects a hex value (no 0x prefix required)\n\n");
				return 2;
			}
			uint32_t m = 0;
			if (!parse_u32_hex(argv[i + 1], &m)) {
				printf("ERROR: invalid nature mask hex: %s\n\n", argv[i + 1]);
				return 2;
			}
			allowed_mod_mask = m;
			i += 1;
			continue;
		}

		printf("ERROR: unknown argument: %s\n\n", argv[i]);
		usage(argv[0]);
		return 2;
	}

	if (!have_daily) {
		printf("ERROR: must provide --daily when using CLI mode\n\n");
		usage(argv[0]);
		return 2;
	}
	if (allowed_mod_mask == 0) {
		printf("ERROR: must provide --nature-idx or --nature-mask\n\n");
		usage(argv[0]);
		return 2;
	}

	// Convert STAT_FLAVOR order (power stamina skill jump speed)
	// to the PID tool order (speed jump skill stamina power).
	int target_bonuses[5] = {
		daily_stat_flavor[4],
		daily_stat_flavor[3],
		daily_stat_flavor[2],
		daily_stat_flavor[1],
		daily_stat_flavor[0],
	};

	// Step 1: precompute the best 5-digit offset (like PID_finder.py)
	uint32_t best_offset = 0;
	uint32_t best_x_mask = 0;
	uint32_t num_offsets = 0;
    uint32_t allowed_x_mask = 0; // 0 means all days allowed
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
		printf("No valid 5-digit offsets found for this criteria.\n");
		return 1;
	}

	printf("Best offset (ranked by streak then count): %05u\n", best_offset);
	printf("Streak: %d\n", best_streak);
	printf("Valid days: %d\n", best_count);
	{
		double prob = ((double)num_offsets * 42950.0) / (double)0xFFFFFFFFu;
		printf("Natural catch probability: %.6f%% (num_offsets=%u)\n", prob * 100.0, num_offsets);
	}
	printXMask(best_x_mask);
	printf("\n");

	uint32_t found_pid = 0;
	uint32_t found_seed = 0;
	int rc = hgssPidSearchForOffsetNoAdvRange(
		best_offset,
		&found_pid,
		&found_seed
	);

	printf("\n");
	if (rc == 0) {
		printf("Best seed: %08x\n", found_seed);
		printf("Best PID:  %08x\n", found_pid);
	}

	// In CLI mode, don't pause for input (so it can be scripted).
	return rc;
}
