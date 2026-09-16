#include <stdint.h>
#include <string.h>

#include "effects.h"
#include "game.h"

GameState game_state;

static uint8_t random_state[4];
static uint8_t group_cells[GAME_BOARD_SIZE];
static uint8_t group_seen[GAME_BOARD_SIZE];

typedef struct OpeningDealWeight {
    uint8_t first;
    uint8_t second;
    uint8_t weight;
} OpeningDealWeight;

/* Probability Table 1: 39 pre-four normal-deal observations. */
static const OpeningDealWeight opening_deal_weights[] = {
    {1u, 0u, 5u}, {2u, 0u, 3u}, {3u, 0u, 1u}, {4u, 0u, 0u},
    {1u, 1u, 0u}, {1u, 2u, 5u}, {1u, 3u, 8u},
    {2u, 1u, 10u}, {2u, 2u, 0u}, {2u, 3u, 1u},
    {3u, 1u, 4u}, {3u, 2u, 2u}, {3u, 3u, 0u},
};

static const uint8_t pair_first[] = {1u, 1u, 2u, 3u, 3u, 3u, 3u, 4u};
static const uint8_t pair_second[] = {2u, 3u, 3u, 1u, 2u, 3u, 4u, 5u};
static const uint8_t other_pair_index[] = {0u, 1u, 2u, 3u, 4u, 6u, 7u};
static const uint8_t pressure_pair_index[] = {0u, 1u, 2u, 3u, 4u, 7u};
static const uint8_t first_callouts[] = {1u, 2u, 4u, 6u, 7u, 8u, 9u};
static const uint8_t score_bonus[] = {0u, 0u, 0u, 0u, 25u, 50u, 100u};

static uint8_t second_cell(uint8_t *index) {
    int8_t x;
    int8_t y;

    x = (int8_t)game_state.cursor_x;
    y = (int8_t)game_state.cursor_y;
    if (game_state.orientation == 0u) {
        ++x;
    } else if (game_state.orientation == 1u) {
        ++y;
    } else if (game_state.orientation == 2u) {
        --x;
    } else {
        --y;
    }
    if (x < 0 || x >= (int8_t)GAME_BOARD_WIDTH || y < 0 || y >= (int8_t)GAME_BOARD_WIDTH) {
        return 0u;
    }
    *index = (uint8_t)((uint8_t)y * GAME_BOARD_WIDTH + (uint8_t)x);
    return 1u;
}

uint16_t game_random16(void) {
    uint16_t sum;
    uint8_t accumulator;
    uint8_t carry;
    uint8_t high;

    sum = (uint16_t)random_state[0] + 0xB3u;
    accumulator = (uint8_t)sum;
    random_state[0] = accumulator;
    carry = (uint8_t)(sum >> 8);

    sum = (uint16_t)accumulator + random_state[1] + carry;
    accumulator = (uint8_t)sum;
    random_state[1] = accumulator;
    carry = (uint8_t)(sum >> 8);

    sum = (uint16_t)accumulator + random_state[2] + carry;
    accumulator = (uint8_t)sum;
    random_state[2] = accumulator;
    carry = (uint8_t)(sum >> 8);

    high = (uint8_t)((accumulator ^ random_state[0]) & 0x7Fu);
    accumulator = random_state[2];
    sum = (uint16_t)accumulator + random_state[3] + carry;
    accumulator = (uint8_t)sum;
    random_state[3] = accumulator;
    accumulator ^= random_state[1];
    return (uint16_t)(((uint16_t)high << 8) | accumulator);
}

uint8_t game_random_mod(uint8_t modulus) {
    return (uint8_t)(game_random16() % modulus);
}

static uint8_t face_is_matching_eligible(uint8_t face, uint8_t four_active) {
    if (face <= 3u) {
        return face != 0u;
    }
    if (face == 4u) {
        return four_active;
    }
    return face == 5u && game_state.five_unlocked;
}

static uint8_t count_empty_neighbors(uint8_t index) {
    uint8_t x;
    uint8_t y;
    uint8_t count;

    x = (uint8_t)(index % GAME_BOARD_WIDTH);
    y = (uint8_t)(index / GAME_BOARD_WIDTH);
    count = 0u;
    if (x && !game_state.board[index - 1u]) ++count;
    if (x + 1u < GAME_BOARD_WIDTH && !game_state.board[index + 1u]) ++count;
    if (y && !game_state.board[index - GAME_BOARD_WIDTH]) ++count;
    if (y + 1u < GAME_BOARD_WIDTH && !game_state.board[index + GAME_BOARD_WIDTH]) ++count;
    return count;
}

static uint8_t matching_single(uint8_t four_active) {
    uint8_t index;
    uint8_t weights[5] = {0u, 0u, 0u, 0u, 0u};
    uint8_t total;
    uint8_t target;

    total = 0u;
    for (index = 0u; index < GAME_BOARD_SIZE; ++index) {
        if (face_is_matching_eligible(game_state.board[index], four_active)) {
            weights[game_state.board[index] - 1u] += count_empty_neighbors(index);
            total = (uint8_t)(total + count_empty_neighbors(index));
        }
    }
    if (!total) {
        return 0u;
    }
    target = game_random_mod(total);
    for (index = 0u; index < 5u; ++index) {
        if (target < weights[index]) {
            game_state.piece_first = index + 1u;
            game_state.piece_second = 0u;
            game_state.piece_count = 1u;
            return 1u;
        }
        target = (uint8_t)(target - weights[index]);
    }
    return 0u;
}

static void uniform_single(uint8_t four_active, uint8_t pressure) {
    static const uint8_t pressure_without_five[] = {1u, 2u, 3u, 3u, 4u, 4u, 4u, 4u, 4u, 4u};
    static const uint8_t pressure_with_five[] = {1u, 2u, 3u, 3u, 4u, 4u, 4u, 4u, 4u, 5u};
    uint8_t count;

    if (pressure) {
        game_state.piece_first = game_state.five_unlocked
            ? pressure_with_five[game_random_mod(10u)]
            : pressure_without_five[game_random_mod(10u)];
    } else {
        count = (uint8_t)(3u + four_active + game_state.five_unlocked);
        game_state.piece_first = (uint8_t)(1u + game_random_mod(count));
        if (!four_active && game_state.piece_first == 4u) game_state.piece_first = 5u;
    }
    game_state.piece_second = 0u;
    game_state.piece_count = 1u;
}

static void opening_piece(void) {
    uint8_t target = game_random_mod(39u);
    uint8_t index;

    for (index = 0u; index < sizeof(opening_deal_weights) / sizeof(opening_deal_weights[0]); ++index) {
        if (target < opening_deal_weights[index].weight) {
            game_state.piece_first = opening_deal_weights[index].first;
            game_state.piece_second = opening_deal_weights[index].second;
            game_state.piece_count = game_state.piece_second ? 2u : 1u;
            return;
        }
        target = (uint8_t)(target - opening_deal_weights[index].weight);
    }
}

static void normal_piece(uint8_t four_active, uint8_t pressure) {
    uint8_t roll;
    uint8_t index;
    uint8_t count;

    if (!four_active && !game_state.five_unlocked) {
        opening_piece();
        return;
    }

    if (game_random_mod(4u) == 0u) {
        uniform_single(four_active, pressure);
        return;
    }

    roll = game_random_mod(15u);
    if (roll == 0u) {
        index = 5u;
    } else if (pressure && roll <= 7u) {
        index = 6u;
    } else if (pressure) {
        count = (uint8_t)(5u + game_state.five_unlocked);
        index = pressure_pair_index[game_random_mod(count)];
    } else {
        count = (uint8_t)(5u + game_state.four_unlocked + game_state.five_unlocked);
        index = other_pair_index[game_random_mod(count)];
        if (!game_state.four_unlocked && index == 6u) index = 7u;
    }
    game_state.piece_first = pair_first[index];
    game_state.piece_second = pair_second[index];
    game_state.piece_count = 2u;
}

static uint8_t board_has_adjacent_empty(void) {
    uint8_t index;
    uint8_t x;
    uint8_t y;

    for (index = 0u; index < GAME_BOARD_SIZE; ++index) {
        if (game_state.board[index]) continue;
        x = (uint8_t)(index % GAME_BOARD_WIDTH);
        y = (uint8_t)(index / GAME_BOARD_WIDTH);
        if (x + 1u < GAME_BOARD_WIDTH && !game_state.board[index + 1u]) return 1u;
        if (y + 1u < GAME_BOARD_WIDTH && !game_state.board[index + GAME_BOARD_WIDTH]) return 1u;
    }
    return 0u;
}

uint8_t game_placement_valid(uint8_t *second_index) {
    uint8_t origin;
    uint8_t second;

    origin = (uint8_t)(game_state.cursor_y * GAME_BOARD_WIDTH + game_state.cursor_x);
    if (game_state.board[origin]) return 0u;
    if (game_state.piece_count == 1u) return 1u;
    if (!second_cell(&second) || game_state.board[second]) return 0u;
    if (second_index) *second_index = second;
    return 1u;
}

static uint8_t seek_valid_placement(void) {
    uint8_t index;

    game_state.cursor_x = 2u;
    game_state.cursor_y = 2u;
    game_state.orientation = 0u;
    if (game_state.piece_count == 2u) return board_has_adjacent_empty();
    for (index = 0u; index < GAME_BOARD_SIZE; ++index) {
        if (!game_state.board[index]) return 1u;
    }
    return 0u;
}

void game_spawn_piece(void) {
    uint8_t occupied;
    uint8_t fours;
    uint8_t index;
    uint8_t pressure;
    uint8_t four_active;
    uint8_t matching_attempt;

    occupied = 0u;
    fours = 0u;
    for (index = 0u; index < GAME_BOARD_SIZE; ++index) {
        if (game_state.board[index]) ++occupied;
        if (game_state.board[index] == 4u) ++fours;
    }
    pressure = fours >= 4u;
    four_active = (uint8_t)(pressure || game_state.four_unlocked);
    matching_attempt = 0u;
    if (!board_has_adjacent_empty()) {
        matching_attempt = 1u;
    } else if (occupied >= 22u) {
        matching_attempt = game_random_mod(4u) != 0u;
    } else if (occupied >= 18u) {
        matching_attempt = game_random_mod(2u) == 0u;
    }

    if (matching_attempt) {
        if (!matching_single(four_active)) uniform_single(four_active, pressure);
    } else {
        normal_piece(four_active, pressure);
        if (game_state.piece_count == 2u && !board_has_adjacent_empty()) {
            if (!matching_single(four_active)) uniform_single(four_active, pressure);
        }
    }
    game_state.game_over = (uint8_t)!seek_valid_placement();
}

static uint8_t collect_group(uint8_t origin) {
    uint8_t face;
    uint8_t head;
    uint8_t tail;
    uint8_t index;
    uint8_t x;
    uint8_t y;
    uint8_t neighbor;

    memset(group_seen, 0, sizeof(group_seen));
    face = game_state.board[origin];
    group_cells[0] = origin;
    group_seen[origin] = 1u;
    head = 0u;
    tail = 1u;
    while (head < tail) {
        index = group_cells[head++];
        x = (uint8_t)(index % GAME_BOARD_WIDTH);
        y = (uint8_t)(index / GAME_BOARD_WIDTH);
        if (x) {
            neighbor = (uint8_t)(index - 1u);
            if (!group_seen[neighbor] && game_state.board[neighbor] == face) {
                group_seen[neighbor] = 1u;
                group_cells[tail++] = neighbor;
            }
        }
        if (x + 1u < GAME_BOARD_WIDTH) {
            neighbor = (uint8_t)(index + 1u);
            if (!group_seen[neighbor] && game_state.board[neighbor] == face) {
                group_seen[neighbor] = 1u;
                group_cells[tail++] = neighbor;
            }
        }
        if (y) {
            neighbor = (uint8_t)(index - GAME_BOARD_WIDTH);
            if (!group_seen[neighbor] && game_state.board[neighbor] == face) {
                group_seen[neighbor] = 1u;
                group_cells[tail++] = neighbor;
            }
        }
        if (y + 1u < GAME_BOARD_WIDTH) {
            neighbor = (uint8_t)(index + GAME_BOARD_WIDTH);
            if (!group_seen[neighbor] && game_state.board[neighbor] == face) {
                group_seen[neighbor] = 1u;
                group_cells[tail++] = neighbor;
            }
        }
    }
    return tail;
}

static void resolve_cell(uint8_t origin) {
    uint8_t face;
    uint8_t count;
    uint8_t index;
    uint8_t callout;
    uint16_t award;

    while (game_state.board[origin]) {
        face = game_state.board[origin];
        count = collect_group(origin);
        if (count < 3u) return;

        if (face == 4u && count >= 4u) game_state.four_unlocked = 1u;
        if (face == 6u && count >= 4u) game_state.five_unlocked = 1u;
        for (index = 0u; index < count; ++index) game_state.board[group_cells[index]] = 0u;
        if (face < 6u) game_state.board[origin] = (uint8_t)(face + 1u);

        ++game_state.merge_depth;
        award = (uint16_t)((uint16_t)face * count + score_bonus[face]);
        award = (uint16_t)(award * game_state.merge_depth);
        game_state.score = (uint16_t)(game_state.score + award);

        if (face == 4u) {
            callout = 3u;
        } else if (face == 5u) {
            callout = 5u;
        } else if (game_state.merge_depth >= 2u) {
            callout = 0u;
        } else {
            callout = first_callouts[game_random_mod(7u)];
        }
        effects_present_merge(face, count, origin, game_state.merge_depth, award, callout);
    }
}

uint8_t game_place_piece(void) {
    uint8_t origin;
    uint8_t second;

    if (game_state.game_over || !game_placement_valid(&second)) return 0u;
    origin = (uint8_t)(game_state.cursor_y * GAME_BOARD_WIDTH + game_state.cursor_x);
    game_state.board[origin] = game_state.piece_first;
    if (game_state.piece_count == 2u) game_state.board[second] = game_state.piece_second;
    game_state.merge_depth = 0u;
    resolve_cell(origin);
    if (game_state.piece_count == 2u && game_state.board[second]) resolve_cell(second);
    game_spawn_piece();
    return 1u;
}

uint8_t game_move_cursor(int8_t delta_x, int8_t delta_y) {
    int8_t x;
    int8_t y;

    x = (int8_t)game_state.cursor_x + delta_x;
    y = (int8_t)game_state.cursor_y + delta_y;
    if (x < 0 || x >= (int8_t)GAME_BOARD_WIDTH || y < 0 || y >= (int8_t)GAME_BOARD_WIDTH) return 0u;
    game_state.cursor_x = (uint8_t)x;
    game_state.cursor_y = (uint8_t)y;
    return 1u;
}

void game_rotate_piece(void) {
    if (game_state.piece_count == 2u) game_state.orientation = (uint8_t)((game_state.orientation + 1u) & 3u);
}

void game_new(uint16_t seed) {
    memset(&game_state, 0, sizeof(game_state));
    random_state[0] = random_state[2] = (uint8_t)seed;
    random_state[1] = random_state[3] = (uint8_t)(seed >> 8);
    game_random16();
    game_spawn_piece();
}
