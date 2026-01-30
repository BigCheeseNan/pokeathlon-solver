from solver_core.constants import intup, MAX_FLAVOR, MAX_TOTAL, EFFECTS


def apply_ingredient(flavors: intup, ingredient: str) -> list[int]:
    effect, candidates = EFFECTS[ingredient]
    new_flavors = [0] * 5
    for i in range(5):
        val = flavors[i] + effect[i]
        if val < 0:
            new_flavors[i] = 0
        elif val > MAX_FLAVOR:
            new_flavors[i] = MAX_FLAVOR
        else:
            new_flavors[i] = val
    total = sum(new_flavors)
    if total > MAX_TOTAL:
        idx = max(candidates, key=lambda i: new_flavors[i])
        new_flavors[idx] = max(0, new_flavors[idx] + MAX_TOTAL - total)
    return new_flavors


def flavors_match(f1: intup, f2: intup) -> bool:
    return all(f1[i] == f2[i] for i in range(5))


def swap_groups(
    grouped: list[tuple[str, int]], i: int, j: int
) -> list[tuple[str, int]]:
    grouped = grouped[:]  # shallow copy
    grouped[i], grouped[j] = grouped[j], grouped[i]
    return grouped


def is_valid_grouping(grouped: list[tuple[str, int]], target: intup) -> bool:
    current = [0] * 5
    for ing, cnt in grouped:
        for _ in range(cnt):
            if ing == "strong" and sum(current) > MAX_TOTAL - 10:
                return False
            current = apply_ingredient(tuple(current), ing)
    return flavors_match(tuple(current), target)


def reduce_recipe(recipe: list[str], target: intup) -> list[tuple[str, int]]:
    if not recipe:
        return []

    # Group consecutive identical ingredients
    grouped = []
    current, count = recipe[0], 1
    for i in range(1, len(recipe)):
        if recipe[i] == current:
            count += 1
        else:
            grouped.append((current, count))
            current, count = recipe[i], 1
    grouped.append((current, count))

    i = 0
    while i < len(grouped) - 2:
        curr = grouped[i][0]
        candidates = [(j, g) for j, g in enumerate(grouped) if g[0] == curr and j > i]
        for j, _ in candidates:
            new_grouped = swap_groups(grouped, i + 1, j)
            if is_valid_grouping(new_grouped, target):
                grouped = new_grouped
                i += 1
        i += 1

    # Merge adjacent identical ingredients
    merged = []
    prev_ing, acc_cnt = grouped[0]
    for ing, cnt in grouped[1:]:
        if ing == prev_ing:
            acc_cnt += cnt
        else:
            merged.append((prev_ing, acc_cnt))
            prev_ing, acc_cnt = ing, cnt
    merged.append((prev_ing, acc_cnt))

    return merged
