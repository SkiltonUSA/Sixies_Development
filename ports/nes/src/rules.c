#include "sixies_rules.h"

#include <string.h>

static uint8_t work_visited[SIXIES_BOARD_CELLS];
static uint8_t work_queue[SIXIES_BOARD_CELLS];
static uint8_t work_group[SIXIES_BOARD_CELLS];

static uint8_t neighbor(uint8_t index, uint8_t orientation)
{
    uint8_t x;
    uint8_t y;

    x = index % SIXIES_BOARD_WIDTH;
    y = index / SIXIES_BOARD_WIDTH;
    if (orientation == 0) {
        return x < 4 ? (uint8_t)(index + 1) : SIXIES_NO_CELL;
    }
    if (orientation == 1) {
        return y < 4 ? (uint8_t)(index + 5) : SIXIES_NO_CELL;
    }
    if (orientation == 2) {
        return x > 0 ? (uint8_t)(index - 1) : SIXIES_NO_CELL;
    }
    return y > 0 ? (uint8_t)(index - 5) : SIXIES_NO_CELL;
}

static uint8_t placement_at(
    const SixiesState* state,
    uint8_t x,
    uint8_t y,
    uint8_t orientation,
    uint8_t piece_count,
    uint8_t* origin_index,
    uint8_t* second_index
)
{
    uint8_t origin;
    uint8_t second;

    *origin_index = SIXIES_NO_CELL;
    *second_index = SIXIES_NO_CELL;
    if (x >= SIXIES_BOARD_WIDTH || y >= SIXIES_BOARD_WIDTH) {
        return 0;
    }

    origin = (uint8_t)(y * SIXIES_BOARD_WIDTH + x);
    *origin_index = origin;
    if (piece_count == 1) {
        return state->board[origin] == 0;
    }

    second = neighbor(origin, orientation);
    *second_index = second;
    if (state->board[origin] != 0 ||
        second == SIXIES_NO_CELL ||
        state->board[second] != 0) {
        return 0;
    }
    return 1;
}

static uint8_t count_fives(const SixiesState* state)
{
    uint8_t index;
    uint8_t count;

    count = 0;
    for (index = 0; index < SIXIES_BOARD_CELLS; ++index) {
        if (state->board[index] == 5) {
            ++count;
        }
    }
    return count;
}

static uint8_t find_group(const SixiesState* state, uint8_t active_index)
{
    static const uint8_t directions[4] = {2, 0, 3, 1};
    uint8_t value;
    uint8_t head;
    uint8_t tail;
    uint8_t count;
    uint8_t current;
    uint8_t candidate;
    uint8_t direction_index;

    memset(work_visited, 0, sizeof(work_visited));
    value = state->board[active_index];
    if (value == 0) {
        return 0;
    }

    head = 0;
    tail = 1;
    count = 0;
    work_queue[0] = active_index;
    work_visited[active_index] = 1;

    while (head < tail) {
        current = work_queue[head++];
        work_group[count++] = current;
        for (direction_index = 0; direction_index < 4; ++direction_index) {
            candidate = neighbor(current, directions[direction_index]);
            if (candidate == SIXIES_NO_CELL || work_visited[candidate]) {
                continue;
            }
            if (state->board[candidate] != value) {
                continue;
            }
            work_visited[candidate] = 1;
            work_queue[tail++] = candidate;
        }
    }
    return count;
}

static void add_merge_event(
    SixiesState* state,
    uint8_t value,
    uint8_t count,
    uint8_t active_index
)
{
    SixiesMergeEvent* event;

    if (state->event_count >= SIXIES_MAX_EVENTS) {
        return;
    }
    event = &state->events[state->event_count++];
    event->value = value;
    event->count = count;
    event->score_delta = (uint8_t)(value * count);
    event->active = active_index;
}

uint8_t sixies_random_byte(SixiesState* state)
{
    uint8_t previous;
    uint8_t next;

    previous = state->rng_state;
    next = (uint8_t)(previous << 1);
    if (previous & 0x80) {
        next ^= 0x1d;
    }
    state->rng_state = next;
    return next;
}

uint8_t sixies_double_space_available(const SixiesState* state)
{
    uint8_t index;
    uint8_t other;

    for (index = 0; index < SIXIES_BOARD_CELLS; ++index) {
        if (state->board[index] != 0) {
            continue;
        }
        other = neighbor(index, 0);
        if (other != SIXIES_NO_CELL && state->board[other] == 0) {
            return 1;
        }
        other = neighbor(index, 1);
        if (other != SIXIES_NO_CELL && state->board[other] == 0) {
            return 1;
        }
    }
    return 0;
}

uint8_t sixies_any_placement(const SixiesState* state, uint8_t piece_count)
{
    uint8_t orientation;
    uint8_t orientation_count;
    uint8_t x;
    uint8_t y;
    uint8_t origin;
    uint8_t second;

    orientation_count = piece_count == 1 ? 1 : 4;
    for (orientation = 0; orientation < orientation_count; ++orientation) {
        for (y = 0; y < SIXIES_BOARD_WIDTH; ++y) {
            for (x = 0; x < SIXIES_BOARD_WIDTH; ++x) {
                if (placement_at(
                        state,
                        x,
                        y,
                        orientation,
                        piece_count,
                        &origin,
                        &second)) {
                    return 1;
                }
            }
        }
    }
    return 0;
}

uint8_t sixies_get_placement(
    const SixiesState* state,
    uint8_t* origin_index,
    uint8_t* second_index
)
{
    return placement_at(
        state,
        state->cursor_x,
        state->cursor_y,
        state->orientation,
        state->piece_count,
        origin_index,
        second_index
    );
}

void sixies_spawn(SixiesState* state)
{
    uint8_t roll;

    state->piece_count = (uint8_t)((sixies_random_byte(state) & 1) + 1);
    state->piece_values[0] = (uint8_t)((sixies_random_byte(state) & 3) + 1);
    state->piece_values[1] = (uint8_t)((sixies_random_byte(state) & 3) + 1);

    if (count_fives(state) >= 5) {
        roll = sixies_random_byte(state);
        if ((roll & 0x0f) == 0) {
            if (state->piece_count == 2) {
                if (sixies_random_byte(state) & 1) {
                    state->piece_values[1] = 5;
                } else {
                    state->piece_values[0] = 5;
                }
            } else {
                state->piece_values[0] = 5;
            }
        }
    }

    if (state->piece_count == 2 &&
        state->piece_values[0] == 4 &&
        state->piece_values[1] == 4) {
        do {
            roll = (uint8_t)(sixies_random_byte(state) & 3);
        } while (roll == 3);
        state->piece_values[1] = (uint8_t)(roll + 1);
    }

    if (state->singles_only || !sixies_double_space_available(state)) {
        state->singles_only = 1;
        state->piece_count = 1;
    }

    state->cursor_x = 2;
    state->cursor_y = 2;
    state->orientation = 0;
    state->game_over = (uint8_t)!sixies_any_placement(state, state->piece_count);
}

void sixies_new_game(SixiesState* state, uint8_t seed)
{
    memset(state, 0, sizeof(*state));
    state->rng_state = seed == 0 ? 1 : seed;
    sixies_spawn(state);
}

void sixies_move_cursor(SixiesState* state, signed char dx, signed char dy)
{
    signed char x;
    signed char y;

    x = (signed char)state->cursor_x + dx;
    y = (signed char)state->cursor_y + dy;
    if (x < 0) {
        x = 0;
    } else if (x >= SIXIES_BOARD_WIDTH) {
        x = SIXIES_BOARD_WIDTH - 1;
    }
    if (y < 0) {
        y = 0;
    } else if (y >= SIXIES_BOARD_WIDTH) {
        y = SIXIES_BOARD_WIDTH - 1;
    }
    state->cursor_x = (uint8_t)x;
    state->cursor_y = (uint8_t)y;
}

void sixies_rotate(SixiesState* state)
{
    if (state->piece_count == 2) {
        state->orientation = (uint8_t)((state->orientation + 1) & 3);
    }
}

void sixies_resolve_at(SixiesState* state, uint8_t active_index)
{
    uint8_t count;
    uint8_t value;
    uint8_t delta;
    uint8_t index;

    while (state->board[active_index] != 0) {
        count = find_group(state, active_index);
        if (count < 3) {
            return;
        }
        value = state->board[active_index];
        delta = (uint8_t)(count * value);
        if (state->score > (uint16_t)(9999 - delta)) {
            state->score = 9999;
        } else {
            state->score = (uint16_t)(state->score + delta);
        }
        add_merge_event(state, value, count, active_index);

        for (index = 0; index < count; ++index) {
            state->board[work_group[index]] = 0;
        }
        if (value == 6) {
            return;
        }
        state->board[active_index] = (uint8_t)(value + 1);
    }
}

uint8_t sixies_place_current(SixiesState* state)
{
    uint8_t origin;
    uint8_t second;

    if (state->game_over || !sixies_get_placement(state, &origin, &second)) {
        return 0;
    }

    state->event_count = 0;
    state->board[origin] = state->piece_values[0];
    if (state->piece_count == 2) {
        state->board[second] = state->piece_values[1];
    }

    sixies_resolve_at(state, origin);
    if (state->piece_count == 2 && state->board[second] != 0) {
        sixies_resolve_at(state, second);
    }
    sixies_spawn(state);
    return 1;
}
