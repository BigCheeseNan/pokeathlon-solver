#define RECIPECALC_EXPORTS
#include "recipe_calculator.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdio.h>
#include <stdint.h>

// Configuration constants
#define INITIAL_NODE_POOL_SIZE 65536        // Starting node pool capacity (2^16)
#define MAX_NODE_POOL_SIZE 134217728         // Maximum node pool capacity (2^27)
#define NODE_POOL_GROWTH_FACTOR 2.0         // Growth multiplier when pool is full
#define INITIAL_HASH_SIZE 262144            // Initial hash table size (2^18)
#define INITIAL_HEAP_SIZE 128               // Initial heap capacity
#define MAX_FLAVOR 63                       // Maximum value for each flavor
#define MAX_TOTAL 100                       // Maximum sum of all flavors
#define STRONG_INGREDIENT_THRESHOLD 90      // Max total before blocking 'strong' ingredient

// Error codes
typedef enum {
    ERR_NO_SOLUTION = -1,
    ERR_INVALID_TARGET = -2,
    ERR_MEMORY_ALLOCATION = -3,
    ERR_NODE_POOL_EXHAUSTED = -4,
    ERR_PATH_TOO_LONG = -5
} ErrorCode;

typedef struct Node {
    int32_t parent_idx; // node index, needs full range
    int32_t heap_idx;   // index in the heap (-1 if not in heap)
    uint8_t flavors[5]; // 0-63, 5 bytes
    uint8_t g;         // cost (0-100 typical), 1 byte
    uint8_t f;         // g + h, 1 byte
    int8_t ingredient;  // ingredient applied (0-6, or -1), 1 byte
    // Total: 4 + 4 + 5 + 1 + 1 + 1 = 16 bytes
} Node;

// Controls whether we prune ingredients to only those affecting the target flavors
static int g_relevant_pruning_enabled = 1;

// Controls whether the solver prints progress information via printf
static int g_verbose_enabled = 1;

static inline uint32_t encode_flavors_u8(const uint8_t f[5]) {
    return  (uint32_t)f[0]
          | ((uint32_t)f[1] << 6)
          | ((uint32_t)f[2] << 12)
          | ((uint32_t)f[3] << 18)
          | ((uint32_t)f[4] << 24);
}

typedef struct {
    uint32_t key;
    int idx;
    uint8_t closed; // whether this node has been expanded
} HashEntry;

#define HASH_EMPTY 0U
#define HASH_LOAD_FACTOR 0.75

typedef struct {
    HashEntry *entries;
    size_t size;
    size_t cap;
} FlavorHash;

// Initialize the hash table
static void hash_init(FlavorHash *h, size_t cap) {
    h->cap = cap;
    h->size = 0;
    h->entries = calloc(cap, sizeof(HashEntry));
}

// Simple mix function for hash keys
static inline uint32_t hash_mix(uint32_t k) {
    k ^= k >> 16;
    k *= 0x45d9f3b;
    k ^= k >> 16;
    k *= 0x45d9f3b;
    k ^= k >> 16;
    return k;
}

// Find a key and mark it closed if found
static int hash_find_and_close_u8(FlavorHash *h, const uint8_t flavors[5], int *out_is_closed) {
    uint32_t key = encode_flavors_u8(flavors);
    size_t mask = h->cap - 1;
    size_t i = hash_mix(key) & mask;
    while (h->entries[i].key != HASH_EMPTY) {
        if (h->entries[i].key == key) {
            *out_is_closed = h->entries[i].closed;
            if (!h->entries[i].closed)
                h->entries[i].closed = 1;
            return h->entries[i].idx;
        }
        i = (i + 1) & mask;
    }
    *out_is_closed = 0;
    return -1;
}

// Find a key and return whether it's closed
static int hash_find_with_closed_u8(const FlavorHash *h, const uint8_t flavors[5], int *out_is_closed) {
    uint32_t key = encode_flavors_u8(flavors);
    size_t mask = h->cap - 1;
    size_t i = hash_mix(key) & mask;
    while (h->entries[i].key != HASH_EMPTY) {
        if (h->entries[i].key == key) {
            *out_is_closed = h->entries[i].closed;
            return h->entries[i].idx;
        }
        i = (i + 1) & mask;
    }
    *out_is_closed = 0;
    return -1;
}

// Reopen a closed entry
static void hash_unclose_u8(FlavorHash *h, const uint8_t flavors[5]) {
    uint32_t key = encode_flavors_u8(flavors);
    size_t mask = h->cap - 1;
    size_t i = hash_mix(key) & mask;
    while (h->entries[i].key != HASH_EMPTY) {
        if (h->entries[i].key == key) {
            h->entries[i].closed = 0;
            return;
        }
        i = (i + 1) & mask;
    }
}

// Insert a new key-index pair into the hash table
static void hash_insert_u8(FlavorHash *h, int idx, const uint8_t flavors[5]) {
    if ((double)(h->size + 1) / h->cap > HASH_LOAD_FACTOR) {
        size_t new_cap = h->cap * 2;
        HashEntry *old = h->entries;
        size_t old_cap = h->cap;
        hash_init(h, new_cap);
        for (size_t i = 0; i < old_cap; i++) {
            if (old[i].key != HASH_EMPTY) {
                uint32_t key = old[i].key;
                size_t mask = h->cap - 1;
                size_t j = hash_mix(key) & mask;
                while (h->entries[j].key != HASH_EMPTY)
                    j = (j + 1) & mask;
                h->entries[j] = old[i];
                h->size++;
            }
        }
        free(old);
    }

    uint32_t key = encode_flavors_u8(flavors);
    size_t mask = h->cap - 1;
    size_t i = hash_mix(key) & mask;
    while (h->entries[i].key != HASH_EMPTY)
        i = (i + 1) & mask;
    h->entries[i].key = key;
    h->entries[i].idx = idx;
    h->entries[i].closed = 0;
    h->size++;
}

// Ingredient effects on flavors
static const int EFFECTS[7][5] = {
    {4, -2, 0, 0, 0},     // spicy
    {0, 4, -2, 0, 0},     // sour
    {0, 0, 4, -2, 0},     // dry
    {0, 0, 0, 4, -2},     // bitter
    {-2, 0, 0, 0, 4},     // sweet
    {-2, -2, -2, -2, -2}, // mild
    {2, 2, 2, 2, 2}       // strong
};

// Per-ingredient overflow reduction candidate indices, -1 terminated
static const int CANDIDATES[7][5] = {
    {1, 2, 3, 4, -1},
    {0, 2, 3, 4, -1},
    {0, 1, 3, 4, -1},
    {0, 1, 2, 4, -1},
    {0, 1, 2, 3, -1},
    {-1, -1, -1, -1, -1},
    {-1, -1, -1, -1, -1}};

// Check if two flavor vectors match
static int flavors_match_u8(const uint8_t a[5], const int b[5]) {
    for (int i = 0; i < 5; i++) {
        if (a[i] != b[i])
            return 0;
    }
    return 1;
}

// Apply an ingredient to a flavor vector, handling overflow reduction
static void apply_ingredient_u8(const uint8_t in[5], int ing, uint8_t out[5]) {
    const int *eff = EFFECTS[ing];
    for (int i = 0; i < 5; i++) {
        int v = (int)in[i] + eff[i];
        if (v < 0)
            v = 0;
        else if (v > MAX_FLAVOR)
            v = MAX_FLAVOR;
        out[i] = v;
    }
    int total = out[0] + out[1] + out[2] + out[3] + out[4];
    if (total > MAX_TOTAL) {
        // choose candidate with max value
        const int *cand = CANDIDATES[ing];
        int reduc_idx = -1;
        int highest_val = -1;
        for (int k = 0; cand[k] != -1; k++) {
            int idx = cand[k];
            if (out[idx] > highest_val) {
                highest_val = out[idx];
                reduc_idx = idx;
            }
        }
        int nv = out[reduc_idx] + MAX_TOTAL - total;
        out[reduc_idx] = nv;
    }
}

static inline void swap_if_less(int *x, int *y) {
    int dx = *x - *y;
    int m = dx >> 31;
    int t = dx & m;
    *x -= t;
    *y += t;
}

static inline int base_bound(const int defs[5]) {
    int a = defs[0], b = defs[1], c = defs[2], d = defs[3], e = defs[4];

    // 5-element sorting network
    swap_if_less(&a, &b);
    swap_if_less(&d, &e);
    swap_if_less(&a, &d);
    swap_if_less(&b, &e);
    swap_if_less(&b, &c);
    swap_if_less(&c, &d);
    swap_if_less(&b, &c);

    if (c == 0)
        return (a + b + 3) >> 2;

    int rounds = (c + 1) >> 1;
    int sub = rounds << 1;

    a = (((a) - sub) & -((a) > sub));
    b = (((b) - sub) & -((b) > sub));
    c = (((c) - sub) & -((c) > sub));
    d = (((d) - sub) & -((d) > sub));
    e = (((e) - sub) & -((e) > sub));

    return rounds + ((a + b + c + d + e + 3) >> 2);
}

// Estimate minimal steps from cur to target
static inline int heuristic_u8(const uint8_t cur[5], const int target[5]) {
    int defs[5];
    int cand[5];
    int cand_count = 0;
    // compute deficits to the target
    for (int i = 0; i < 5; i++) {
        int d = target[i] - (int)cur[i];
        if (d < 0)
            d = 0;
        defs[i] = d;
        // find even flavors with an odd target
        if ((target[i] & 1) && !(cur[i] & 1))
            cand[cand_count++] = i;
    }
    if (cand_count == 0)
        return base_bound(defs);
    
    // Sort candidates by (MAX_FLAVOR - target[i]) ascending (insertion sort for small array)
    for (int i = 1; i < cand_count; i++) {
        int key = cand[i];
        int key_val = MAX_FLAVOR - target[key];
        int j = i - 1;
        while (j >= 0 && (MAX_FLAVOR - target[cand[j]]) > key_val) {
            cand[j + 1] = cand[j];
            j--;
        }
        cand[j + 1] = key;
    }
    
    // Apply penalty to first (cand_count + 1) / 2 candidates
    int penalty_count = (cand_count + 1) / 2;
    for (int k = 0; k < penalty_count; k++) {
        int idx = cand[k];
        defs[idx] = MAX_FLAVOR - cur[idx];
    }
    
    return base_bound(defs);
}

// Simple open list (binary heap)
typedef struct
{
    int *idxs;
    int size;
    int cap;
    Node *nodes;
} OpenHeap;

// Initialize the binary heap for the open list
static void heap_init(OpenHeap *h, Node *nodes) {
    h->idxs = NULL;
    h->size = 0;
    h->cap = 0;
    h->nodes = nodes;
}

// Bubble up element at position p to maintain heap property
static void heap_bubble_up(OpenHeap *h, int p) {
    while (p > 0) {
        int parent = (p - 1) / 2;
        if (h->nodes[h->idxs[parent]].f <= h->nodes[h->idxs[p]].f)
            break;
        int tmp = h->idxs[parent];
        h->idxs[parent] = h->idxs[p];
        h->idxs[p] = tmp;
        h->nodes[h->idxs[p]].heap_idx = p;
        h->nodes[h->idxs[parent]].heap_idx = parent;
        p = parent;
    }
}

// Bubble down element at position p to maintain heap property
static void heap_bubble_down(OpenHeap *h, int p) {
    while (1) {
        int l = 2 * p + 1;
        if (l >= h->size)
            break;
        int r = l + 1;
        int s = l;
        if (r < h->size && h->nodes[h->idxs[r]].f < h->nodes[h->idxs[l]].f)
            s = r;
        if (h->nodes[h->idxs[p]].f <= h->nodes[h->idxs[s]].f)
            break;
        int tmp = h->idxs[p];
        h->idxs[p] = h->idxs[s];
        h->idxs[s] = tmp;
        h->nodes[h->idxs[p]].heap_idx = p;
        h->nodes[h->idxs[s]].heap_idx = s;
        p = s;
    }
}

// Push a node index onto the open heap, maintaining heap order by f value
// Returns 0 on success, -1 on allocation failure
static int heap_push(OpenHeap *h, int idx) {
    if (h->size == h->cap) {
        int new_cap = h->cap ? h->cap * 2 : INITIAL_HEAP_SIZE;
        int *new_idxs = (int *)realloc(h->idxs, new_cap * sizeof(int));
        if (!new_idxs)
            return -1; // Allocation failed
        h->idxs = new_idxs;
        h->cap = new_cap;
    }
    int p = h->size++;
    h->idxs[p] = idx;
    h->nodes[idx].heap_idx = p;
    heap_bubble_up(h, p);
    return 0;
}

// Update heap after decreasing the f value of a node
static void heap_decrease_key(OpenHeap *h, int idx) {
    int p = h->nodes[idx].heap_idx;
    if (p >= 0 && p < h->size)
        heap_bubble_up(h, p);
}

// Pop the node index with the lowest f value from the open heap
static int heap_pop(OpenHeap *h) {
    if (!h->size)
        return -1;
    int ret = h->idxs[0];
    h->nodes[ret].heap_idx = -1;
    h->size--;
    if (h->size) {
        h->idxs[0] = h->idxs[h->size];
        h->nodes[h->idxs[0]].heap_idx = 0;
        heap_bubble_down(h, 0);
    }
    return ret;
}

// Public toggle for ingredient pruning
RECIPEC_API void recipe_calc_set_relevant_pruning(int enabled) {
    g_relevant_pruning_enabled = enabled ? 1 : 0;
}

// Public toggle for printf progress output
RECIPEC_API void recipe_calc_set_verbose(int enabled) {
    g_verbose_enabled = enabled ? 1 : 0;
}


// A* search for minimal ingredient sequence to reach target flavor vector from [0,0,0,0,0].
// Returns number of steps, or negative error code. Fills steps_out with ingredient indices.
RECIPEC_API int astar_minimal_recipe_c(const int target[5], int *steps_out, int max_steps) {
    // validate target
    int total = 0;
    for (int i = 0; i < 5; i++) {
        if (target[i] < 0 || target[i] > MAX_FLAVOR)
            return ERR_INVALID_TARGET;
        total += target[i];
    }
    if (total > MAX_TOTAL)
        return ERR_INVALID_TARGET;

    // Allocate data structures with initial capacity
    int node_pool_capacity = INITIAL_NODE_POOL_SIZE;
    if (g_verbose_enabled)
        printf("Allocating initial node pool: %d nodes (%zu bytes)\n", node_pool_capacity, sizeof(Node) * node_pool_capacity);
    Node *nodes = (Node *)calloc(node_pool_capacity, sizeof(Node));
    FlavorHash table;
    hash_init(&table, INITIAL_HASH_SIZE);
    if (!nodes || !table.entries) {
        printf("ERROR: Node pool or hash allocation failed!\n");
        if (nodes)
            free(nodes);
        if (table.entries)
            free(table.entries);
        return ERR_MEMORY_ALLOCATION;
    }
    int node_count = 0;
    int reopened_count = 0;
    OpenHeap open;
    heap_init(&open, nodes);

    Node start;
    memset(&start, 0, sizeof(start));
    start.g = 0;
    start.f = heuristic_u8(start.flavors, target);
    start.parent_idx = -1;
    start.ingredient = -1;
    start.heap_idx = -1;
    nodes[node_count] = start;
    if (heap_push(&open, node_count) != 0) {
        printf("ERROR: Failed to push start node to heap!\n");
        free(nodes);
        free(table.entries);
        return ERR_MEMORY_ALLOCATION;
    }
    node_count++;

    int goal_idx = -1;
    int relevant_ingredients[7];
    int relevant_count = 0;
    if (g_relevant_pruning_enabled) {
        // Compute relevant ingredients: those affecting nonzero target flavors, plus mild and strong
        for (int i = 0; i < 5; i++) {
            if (target[i] > 0)
                relevant_ingredients[relevant_count++] = i; // ingredient index matches flavor index for first 5
        }
        relevant_ingredients[relevant_count++] = 5; // mild
        relevant_ingredients[relevant_count++] = 6; // strong
    }
    else {
        for (int i = 0; i < 7; i++)
            relevant_ingredients[relevant_count++] = i;
    }

    while (open.size) {
        int idx = heap_pop(&open);
        
        // Check if already expanded and mark as closed in one operation
        int is_closed;
        hash_find_and_close_u8(&table, nodes[idx].flavors, &is_closed);
        if (is_closed)
            continue;
        
        // Quick goal test: if h=0, we're at target (avoids computing h again)
        int h = nodes[idx].f - nodes[idx].g;
        if (h == 0 && flavors_match_u8(nodes[idx].flavors, target)) {
            goal_idx = idx;
            break;
        }
        
        // expand
        for (int k = 0; k < relevant_count; k++) {
            int ing = relevant_ingredients[k];
            if (ing == 6) { // strong constraint
                int sum = nodes[idx].flavors[0] + nodes[idx].flavors[1] + nodes[idx].flavors[2] + nodes[idx].flavors[3] + nodes[idx].flavors[4];
                if (sum > STRONG_INGREDIENT_THRESHOLD)
                    continue;
            }
            uint8_t nf[5];
            apply_ingredient_u8(nodes[idx].flavors, ing, nf);
            
            int is_closed;
            int existing = hash_find_with_closed_u8(&table, nf, &is_closed);
            int tentative_g = nodes[idx].g + 1;
            if (existing >= 0) {
                // Node already exists - check if we found a better path
                if (tentative_g < nodes[existing].g) {
                    // Found better path - update the node
                    nodes[existing].g = tentative_g;
                    nodes[existing].f = tentative_g + heuristic_u8(nf, target);
                    nodes[existing].parent_idx = idx;
                    nodes[existing].ingredient = ing;
                    
                    if (is_closed) {
                        // Node was closed - reopen it
                        hash_unclose_u8(&table, nf);
                        if (heap_push(&open, existing) != 0) {
                            printf("ERROR: Failed to push reopened node to heap!\n");
                            free(open.idxs);
                            free(nodes);
                            free(table.entries);
                            return ERR_MEMORY_ALLOCATION;
                        }
                        reopened_count++;
                    }
                    else {
                        // Node is still in open list - just update its position
                        heap_decrease_key(&open, existing);
                    }
                }
            }
            else {
                // Create new node - grow pool if needed
                if (node_count >= node_pool_capacity) {
                    if (node_pool_capacity >= MAX_NODE_POOL_SIZE) {
                        printf("ERROR: Node pool exhausted at maximum size %d nodes!\n", node_pool_capacity);
                        free(open.idxs);
                        free(nodes);
                        free(table.entries);
                        return ERR_NODE_POOL_EXHAUSTED;
                    }
                    
                    // Grow the pool
                    size_t new_capacity = (size_t)(node_pool_capacity * NODE_POOL_GROWTH_FACTOR);
                    if (new_capacity > MAX_NODE_POOL_SIZE)
                        new_capacity = MAX_NODE_POOL_SIZE;
                    
                          if (g_verbose_enabled)
                           printf("Growing node pool from %d to %zu nodes (%zu bytes)\n",
                               node_pool_capacity, new_capacity, sizeof(Node) * new_capacity);
                    
                    Node *new_nodes = (Node *)realloc(nodes, new_capacity * sizeof(Node));
                    if (!new_nodes) {
                        printf("ERROR: Failed to grow node pool!\n");
                        free(open.idxs);
                        free(nodes);
                        free(table.entries);
                        return ERR_MEMORY_ALLOCATION;
                    }
                    
                    // Zero out the new portion
                    memset(new_nodes + node_pool_capacity, 0, (new_capacity - node_pool_capacity) * sizeof(Node));
                    
                    nodes = new_nodes;
                    open.nodes = nodes; // Update heap's pointer to nodes
                    node_pool_capacity = (int)new_capacity;
                }
                
                Node n;
                for (int i = 0; i < 5; i++)
                    n.flavors[i] = nf[i];
                n.g = tentative_g;
                n.f = tentative_g + heuristic_u8(n.flavors, target);
                n.parent_idx = idx;
                n.ingredient = ing;
                n.heap_idx = -1;
                nodes[node_count] = n;
                hash_insert_u8(&table, node_count, n.flavors);
                if (heap_push(&open, node_count) != 0) {
                    printf("ERROR: Failed to push node to heap!\n");
                    free(open.idxs);
                    free(nodes);
                    free(table.entries);
                    return ERR_MEMORY_ALLOCATION;
                }
                node_count++;
            }
        }
    }
    if (g_verbose_enabled) {
        printf("Final node count: %d\n", node_count);
        printf("Nodes reopened: %d\n", reopened_count);
    }

    int result = ERR_NO_SOLUTION;
    if (goal_idx >= 0) {
        // reconstruct path
        int path_len = 0;
        int cur = goal_idx;
        while (cur != -1) {
            if (nodes[cur].ingredient != -1)
                path_len++;
            cur = nodes[cur].parent_idx;
        }
        if (path_len > max_steps)
            result = ERR_PATH_TOO_LONG;
        else {
            int write = path_len - 1;
            cur = goal_idx;
            while (cur != -1) {
                int ing = nodes[cur].ingredient;
                if (ing != -1)
                    steps_out[write--] = ing;
                cur = nodes[cur].parent_idx;
            }
            result = path_len;
        }
    }

    free(open.idxs);
    free(nodes);
    free(table.entries);
    return result;
}
