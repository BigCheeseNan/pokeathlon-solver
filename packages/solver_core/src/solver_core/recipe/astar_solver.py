import heapq
import math
import time
from solver_core.recipe.reduce import reduce_recipe
from solver_core.constants import intup, INGREDIENTS, MAX_FLAVOR, MAX_TOTAL, EFFECTS


def apply_ingredient(flavors: intup, ingredient: str) -> list[int]:
    effect, candidates = EFFECTS[ingredient]
    new_flavors = [min(MAX_FLAVOR, max(0, f + e)) for f, e in zip(flavors, effect)]
    total = sum(new_flavors)
    if total > MAX_TOTAL and candidates:
        idx = max(candidates, key=lambda i: new_flavors[i])
        excess = total - MAX_TOTAL
        new_flavors[idx] = max(0, new_flavors[idx] - excess)
    return new_flavors


def flavors_match(f1: intup, f2: intup) -> bool:
    return all(f1[i] == f2[i] for i in range(5))


def base_bound(deficits: list[int]) -> int:
    d = sorted(deficits, reverse=True)
    if d[2] == 0:  # if third val is 0 then best possible step is 4
        return math.ceil(sum(d) / 4)
    # else use strong ingredient up to the third highest flavor
    rounds = math.ceil(d[2] / 2)
    # and then fall back to step of 4
    residuals = [max(0, x - 2 * rounds) for x in d]
    return rounds + math.ceil(sum(residuals) / 4)


def heuristic(flavors: intup, target: intup) -> int:
    deficits = []
    candidates = []

    for i, (f, t) in enumerate(zip(flavors, target)):
        deficits.append(max(0, t - f))
        if t % 2 == 1 and f % 2 == 0:
            candidates.append(i)

    if not candidates:
        return base_bound(deficits)

    penalty_count = (len(candidates) + 1) // 2
    candidates.sort(key=lambda i: MAX_FLAVOR - target[i])

    for i in candidates[:penalty_count]:
        deficits[i] = MAX_FLAVOR - flavors[i]

    return base_bound(deficits)


def astar_minimal_recipe(
    target_flavors: intup, start=(0, 0, 0, 0, 0), prune: bool = True
) -> list[str] | None:

    if flavors_match(start, target_flavors):
        return []

    # Priority queue: (f, g, state)
    open_heap: list[tuple[int, int, intup]] = []
    heapq.heappush(open_heap, (heuristic(start, target_flavors), 0, start))
    came_from: dict[intup, tuple[intup, str]] = {}
    g_score = {start: 0}
    closed: set[intup] = set()

    required_indices = [i for i, f in enumerate(target_flavors) if f > 0]
    relevant_ingredients = [INGREDIENTS[i] for i in required_indices] + [
        "mild",
        "strong",
    ]

    node_count = 0
    reopened_count = 0

    while open_heap:
        _, g, state = heapq.heappop(open_heap)
        # Only add to closed when expanding with lowest cost
        if state in closed:
            # If this state is in closed but we found a better g, reopen it
            if g > g_score.get(state, float("inf")):
                continue
            # else, allow reopening
        closed.add(state)

        if flavors_match(state, target_flavors):
            path: list[str] = []
            while state != start:
                state, ing = came_from[state]
                path.append(ing)
            print(f"Total nodes explored: {node_count}")
            print(f"Total nodes reopened: {reopened_count}")
            return path[::-1]

        if prune:
            ingredients_to_use = relevant_ingredients
        else:
            ingredients_to_use = INGREDIENTS

        for ing in ingredients_to_use:
            if (
                sum([min(f + 2, MAX_FLAVOR) for f in state]) > MAX_TOTAL
                and ing == "strong"
            ):
                continue
            new_state = tuple(apply_ingredient(state, ing))
            tentative_g = g + 1
            if tentative_g < g_score.get(new_state, float("inf")):
                g_score[new_state] = tentative_g
                came_from[new_state] = (state, ing)
                f = tentative_g + heuristic(new_state, target_flavors)
                heapq.heappush(open_heap, (f, tentative_g, new_state))
                node_count += 1
                # If new_state was in closed but we found a better path, remove from closed and count as reopened
                if new_state in closed:
                    closed.remove(new_state)
                    reopened_count += 1

    print(f"Total nodes explored: {node_count}")
    print(f"Total nodes reopened: {reopened_count}")
    return None


def is_possible_flavor(target_flavors: intup) -> bool:
    if any(f < 0 or f > MAX_FLAVOR for f in target_flavors):
        return False
    if sum(target_flavors) > MAX_TOTAL:
        return False
    return True


if __name__ == "__main__":
    # "power", "stamina", "skill", "jump", "speed"
    targets = [
        # (50, 50, 0, 0, 0),
        # # this one is not optimal with relevant_ingredient pruning (+1)
        # (50, 0, 50, 0, 0),
        # (0, 0, 50, 0, 50),
        # (50, 0, 0, 0, 50),
        # (0, 48, 0, 0, 52),
        # (0, 0, 0, 30, 50), #j1
        # (0, 0, 48, 0, 50), #j2
        # (0, 0, 49, 0, 51),
        # (49, 51, 0, 0, 0),
        # (49, 0, 51, 0, 0),
        # (0, 0, 49, 50, 1),
        # (49, 50, 0, 0, 1),
        # # this one takes too long (80 seconds), the heuristic is off by a lot (still faster than BFS though)
        (49, 49, 0, 1, 1),
        # (1, 1, 1, 1, 1),
        # (1, 1, 1, 1, 0),
        # (63, 1, 1, 1, 1),
        # (48, 0, 0, 0, 48), # Stamina (feed all 3)
        # (0, 0, 48, 0, 52), # Skill (feed 2, reset, feed 1)
        # (0, 0, 48, 0, 52), # Speed (feed 1, reset, feed 2)
        # (0, 0, 48, 0, 52), # Power (reset, feed 2, reset, feed 1)
        # (0, 0, 48, 0, 52), # Jump (feed 1, transition: 6x bitter, 4x sweet)
        # (0, 0, 0, 24, 44), # Jump (feed 2)
    ]
    for target in targets:
        print(f"Target flavors: {target}")
        start = (0, 0, 0, 0, 0)
        # start = (48, 0, 0, 0, 48)
        print("Heuristic to target:", heuristic(start, target))
        start_time = time.time()
        if is_possible_flavor(target):
            recipe = astar_minimal_recipe(target, start, prune=True)
            elapsed = time.time() - start_time
            if recipe:
                grouped = reduce_recipe(recipe, target)
                for ing, cnt in grouped:
                    print(f"{ing} x{cnt}", end=", ")
                print(f"Total ingredients: {len(recipe)}")
            else:
                print("No recipe found.")
            print(f"Time taken: {elapsed:.3f} seconds\n")
        else:
            elapsed = time.time() - start_time
            print("Target flavors are not possible.")
            print(f"Time taken: {elapsed:.3f} seconds")
