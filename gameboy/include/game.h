#ifndef SIXIES_GAME_H
#define SIXIES_GAME_H

#include <stdint.h>

#define GAME_BOARD_WIDTH 5u
#define GAME_BOARD_SIZE 25u

typedef struct GameState {
    uint8_t board[GAME_BOARD_SIZE];
    uint8_t piece_first;
    uint8_t piece_second;
    uint8_t piece_count;
    uint8_t cursor_x;
    uint8_t cursor_y;
    uint8_t orientation;
    uint8_t four_unlocked;
    uint8_t five_unlocked;
    uint8_t game_over;
    uint8_t merge_depth;
    uint16_t score;
} GameState;

extern GameState game_state;

void game_new(uint16_t seed);
void game_spawn_piece(void);
uint8_t game_move_cursor(int8_t delta_x, int8_t delta_y);
void game_rotate_piece(void);
uint8_t game_placement_valid(uint8_t *second_index);
uint8_t game_place_piece(void);
uint16_t game_random16(void);
uint8_t game_random_mod(uint8_t modulus);

#endif
