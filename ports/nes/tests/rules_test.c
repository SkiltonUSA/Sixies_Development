#include "sixies_rules.h"

#include <stdio.h>
#include <string.h>

static unsigned failures;

#define CHECK(condition, message) \
    do { \
        if (!(condition)) { \
            fprintf(stderr, "FAIL: %s\n", message); \
            ++failures; \
        } \
    } while (0)

static void clear_state(SixiesState* state)
{
    memset(state, 0, sizeof(*state));
    state->rng_state = 1;
    state->piece_count = 1;
}

static void test_placement(void)
{
    SixiesState state;
    uint8_t origin;
    uint8_t second;

    clear_state(&state);
    state.piece_count = 2;
    state.piece_values[0] = 2;
    state.piece_values[1] = 3;
    state.cursor_x = 4;
    state.cursor_y = 4;
    CHECK(!sixies_get_placement(&state, &origin, &second), "double cannot cross right edge");
    CHECK(origin == 24 && second == SIXIES_NO_CELL, "edge placement reports indices");

    state.cursor_x = 1;
    state.cursor_y = 1;
    state.orientation = 1;
    CHECK(sixies_get_placement(&state, &origin, &second), "double can face down");
    CHECK(origin == 6 && second == 11, "down placement indices match contract");

    state.board[6] = 4;
    state.orientation = 0;
    CHECK(!sixies_get_placement(&state, &origin, &second), "occupied double origin is blocked");
    CHECK(origin == 6 && second == 7, "blocked double still reports its second target");
}

static void test_merges(void)
{
    SixiesState state;

    clear_state(&state);
    state.board[11] = 1;
    state.board[12] = 1;
    state.board[13] = 1;
    sixies_resolve_at(&state, 12);
    CHECK(state.board[12] == 2, "three ones upgrade at active cell");
    CHECK(state.score == 3, "three ones score three");
    CHECK(state.event_count == 1 && state.events[0].count == 3, "merge emits one event");

    clear_state(&state);
    state.board[0] = 1;
    state.board[6] = 1;
    state.board[12] = 1;
    sixies_resolve_at(&state, 6);
    CHECK(state.score == 0 && state.board[6] == 1, "diagonal dice do not merge");

    clear_state(&state);
    state.board[7] = 2;
    state.board[11] = 1;
    state.board[12] = 1;
    state.board[13] = 1;
    state.board[17] = 2;
    sixies_resolve_at(&state, 12);
    CHECK(state.board[12] == 3 && state.score == 9, "chain resolves ones through twos");
    CHECK(state.event_count == 2 && state.events[1].value == 2, "chain events remain ordered");

    clear_state(&state);
    state.score = 9995;
    state.board[0] = 6;
    state.board[1] = 6;
    state.board[2] = 6;
    sixies_resolve_at(&state, 1);
    CHECK(state.score == 9999, "score saturates at 9999");
    CHECK(state.board[0] == 0 && state.board[1] == 0 && state.board[2] == 0,
          "merged sixes disappear");
}

static void test_origin_first_double(void)
{
    SixiesState state;

    clear_state(&state);
    state.board[2] = 2;
    state.board[5] = 1;
    state.board[11] = 1;
    state.piece_count = 2;
    state.piece_values[0] = 1;
    state.piece_values[1] = 2;
    state.cursor_x = 1;
    state.cursor_y = 1;
    CHECK(sixies_place_current(&state), "origin-first double placement succeeds");
    CHECK(state.board[6] == 3 && state.score == 9, "origin fully resolves before second cell");
    CHECK(state.event_count == 2, "origin-first chain emits both events");
}

static void test_spawning(void)
{
    SixiesState state;
    uint8_t index;

    clear_state(&state);
    sixies_spawn(&state);
    CHECK(state.piece_count == 1, "seed 1 spawns a single");
    CHECK(state.piece_values[0] == 1 && state.piece_values[1] == 1,
          "single still consumes both value rolls");
    CHECK(state.rng_state == 8, "seed 1 call order is stable");

    clear_state(&state);
    state.rng_state = 129;
    sixies_spawn(&state);
    CHECK(state.piece_count == 2, "seed 129 spawns a double");
    CHECK(state.piece_values[0] == 3 && state.piece_values[1] == 1,
          "seed 129 values match contract");
    CHECK(state.rng_state == 124, "seed 129 call order is stable");

    clear_state(&state);
    for (index = 0; index < SIXIES_BOARD_CELLS; ++index) {
        state.board[index] = 1;
    }
    state.rng_state = 129;
    sixies_spawn(&state);
    CHECK(state.singles_only && state.game_over, "full board forces singles and game over");
}

int main(void)
{
    test_placement();
    test_merges();
    test_origin_first_double();
    test_spawning();

    if (failures != 0) {
        fprintf(stderr, "FAILED: %u portable rules checks\n", failures);
        return 1;
    }
    puts("PASS: portable Sixies C rules shell");
    return 0;
}
