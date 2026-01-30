#ifndef RECIPE_CALCULATOR_H
#define RECIPE_CALCULATOR_H


#ifdef RECIPECALC_NO_DLL
#  define RECIPEC_API
#else
#  ifdef _WIN32
#    ifdef RECIPECALC_EXPORTS
#      define RECIPEC_API __declspec(dllexport)
#    else
#      define RECIPEC_API __declspec(dllimport)
#    endif
#  else
#    define RECIPEC_API
#  endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

// Ingredient indices
// 0 spicy, 1 sour, 2 dry, 3 bitter, 4 sweet, 5 mild, 6 strong

// Run A* to find minimal recipe. Returns number of steps (<= max_steps) or -1 none, -2 invalid target, -3 overflow.
RECIPEC_API int astar_minimal_recipe_c(const int target[5], int *steps_out, int max_steps);
RECIPEC_API void recipe_calc_set_relevant_pruning(int enabled);
RECIPEC_API void recipe_calc_set_verbose(int enabled);

#ifdef __cplusplus
}
#endif

#endif