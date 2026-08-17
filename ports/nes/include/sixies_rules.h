#ifndef SIXIES_RULES_H
#define SIXIES_RULES_H

#include <stdint.h>

#define SIXIES_BOARD_WIDTH 5
#define SIXIES_BOARD_CELLS 25
#define SIXIES_MAX_EVENTS 12
#define SIXIES_NO_CELL 0xff

typedef struct SixiesMergeEvent {
    uint8_t value;
    uint8_t count;
    uint8_t score_delta;
    uint8_t active;
} SixiesMergeEvent;

typedef struct SixiesState {
    uint8_t board[SIXIES_BOARD_CELLS];
    uint16_t score;
    uint8_t piece_count;
    uint8_t piece_values[2];
    uint8_t cursor_x;
    uint8_t cursor_y;
    uint8_t orientation;
    uint8_t rng_state;
    uint8_t singles_only;
    uint8_t game_over;
    uint8_t event_count;
    SixiesMergeEvent events[SIXIES_MAX_EVENTS];
} SixiesState;

void sixies_new_game(SixiesState* state, uint8_t seed);
void sixies_spawn(SixiesState* state);
uint8_t sixies_random_byte(SixiesState* state);
uint8_t sixies_get_placement(
    const SixiesState* state,
    uint8_t* origin_index,
    uint8_t* second_index
);
uint8_t sixies_any_placement(const SixiesState* state, uint8_t piece_count);
uint8_t sixies_double_space_available(const SixiesState* state);
void sixies_move_cursor(SixiesState* state, signed char dx, signed char dy);
void sixies_rotate(SixiesState* state);
uint8_t sixies_place_current(SixiesState* state);
void sixies_resolve_at(SixiesState* state, uint8_t active_index);

#endif
