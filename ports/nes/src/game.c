#include "sixies_rules.h"

#include <joystick.h>
#include <nes.h>
#include <stdint.h>
#include <string.h>

#define BOARD_LEFT 4
#define BOARD_TOP 4
#define BOARD_TILE_SIZE 21
#define CELL_TILE_SIZE 4
#define NEXT_LEFT 28
#define NEXT_TOP 8
#define NAMETABLE_WIDTH 32
#define NAMETABLE_HEIGHT 30
#define NAMETABLE_SIZE 960
#define ATTRIBUTE_SIZE 64
#define DIE_BASE 92
#define DIE_TILES_PER_STYLE 54

#define TILE_BLANK 0
#define TILE_GRID_HORIZONTAL 1
#define TILE_GRID_VERTICAL 2
#define TILE_GRID_CROSS 3
#define TILE_GRID_TOP 4
#define TILE_GRID_BOTTOM 5
#define TILE_GRID_LEFT 6
#define TILE_GRID_RIGHT 7
#define TILE_GRID_TOP_LEFT 8
#define TILE_GRID_TOP_RIGHT 9
#define TILE_GRID_BOTTOM_LEFT 10
#define TILE_GRID_BOTTOM_RIGHT 11

#define STYLE_NORMAL 0
#define STYLE_PREVIEW 1
#define STYLE_INVALID 2

#define DIR_MASK (JOY_UP_MASK | JOY_DOWN_MASK | JOY_LEFT_MASK | JOY_RIGHT_MASK)

enum ShellMessage {
    MESSAGE_READY,
    MESSAGE_BLOCKED,
    MESSAGE_MERGED,
    MESSAGE_NEW_GAME,
    MESSAGE_UI_TODO
};

static const uint8_t palette_data[32] = {
    0x0f, 0x00, 0x20, 0x21,
    0x0f, 0x00, 0x2a, 0x24,
    0x0f, 0x00, 0x28, 0x27,
    0x0f, 0x00, 0x10, 0x16,
    0x0f, 0x00, 0x20, 0x21,
    0x0f, 0x00, 0x2a, 0x24,
    0x0f, 0x00, 0x28, 0x27,
    0x0f, 0x00, 0x10, 0x16
};

static SixiesState game;
static uint8_t nametable[NAMETABLE_SIZE];
static uint8_t attributes[ATTRIBUTE_SIZE];
static uint8_t shell_message;
static uint8_t frame_counter;
static uint8_t repeat_counter;

static void set_tile(uint8_t x, uint8_t y, uint8_t tile)
{
    if (x < NAMETABLE_WIDTH && y < NAMETABLE_HEIGHT) {
        nametable[(uint16_t)y * NAMETABLE_WIDTH + x] = tile;
    }
}

static void draw_text(uint8_t x, uint8_t y, const char* text)
{
    while (*text != '\0' && x < NAMETABLE_WIDTH) {
        set_tile(x++, y, (uint8_t)*text++);
    }
}

static void draw_score(uint8_t x, uint8_t y, uint16_t score)
{
    char digits[5];

    digits[4] = '\0';
    digits[3] = (char)('0' + score % 10);
    score /= 10;
    digits[2] = (char)('0' + score % 10);
    score /= 10;
    digits[1] = (char)('0' + score % 10);
    score /= 10;
    digits[0] = (char)('0' + score % 10);
    draw_text(x, y, digits);
}

static uint8_t palette_for_value(uint8_t value)
{
    if (value <= 2) {
        return 0;
    }
    if (value <= 4) {
        return 1;
    }
    return 2;
}

static void set_attribute_block(uint8_t tile_x, uint8_t tile_y, uint8_t palette)
{
    uint8_t index;

    index = (uint8_t)((tile_y / 4) * 8 + tile_x / 4);
    attributes[index] = (uint8_t)(palette * 0x55);
}

static void draw_die(uint8_t x, uint8_t y, uint8_t value, uint8_t style)
{
    uint8_t position;
    uint8_t tile;

    for (position = 0; position < 9; ++position) {
        tile = (uint8_t)(DIE_BASE + style * DIE_TILES_PER_STYLE +
                         (value - 1) * 9 + position);
        set_tile((uint8_t)(x + position % 3),
                 (uint8_t)(y + position / 3),
                 tile);
    }
}

static void set_cell_palette(uint8_t index, uint8_t palette)
{
    uint8_t x;
    uint8_t y;

    x = (uint8_t)(BOARD_LEFT + (index % 5) * CELL_TILE_SIZE);
    y = (uint8_t)(BOARD_TOP + (index / 5) * CELL_TILE_SIZE);
    set_attribute_block(x, y, palette);
}

static void draw_grid(void)
{
    uint8_t x;
    uint8_t y;
    uint8_t relative_x;
    uint8_t relative_y;
    uint8_t tile;

    for (y = BOARD_TOP; y < BOARD_TOP + BOARD_TILE_SIZE; ++y) {
        relative_y = (uint8_t)(y - BOARD_TOP);
        for (x = BOARD_LEFT; x < BOARD_LEFT + BOARD_TILE_SIZE; ++x) {
            relative_x = (uint8_t)(x - BOARD_LEFT);
            if (relative_x % CELL_TILE_SIZE == 0 && relative_y % CELL_TILE_SIZE == 0) {
                tile = TILE_GRID_CROSS;
                if (relative_y == 0) {
                    tile = relative_x == 0 ? TILE_GRID_TOP_LEFT :
                        (relative_x == BOARD_TILE_SIZE - 1 ?
                         TILE_GRID_TOP_RIGHT : TILE_GRID_TOP);
                } else if (relative_y == BOARD_TILE_SIZE - 1) {
                    tile = relative_x == 0 ? TILE_GRID_BOTTOM_LEFT :
                        (relative_x == BOARD_TILE_SIZE - 1 ?
                         TILE_GRID_BOTTOM_RIGHT : TILE_GRID_BOTTOM);
                } else if (relative_x == 0) {
                    tile = TILE_GRID_LEFT;
                } else if (relative_x == BOARD_TILE_SIZE - 1) {
                    tile = TILE_GRID_RIGHT;
                }
                set_tile(x, y, tile);
            } else if (relative_y % CELL_TILE_SIZE == 0) {
                set_tile(x, y, TILE_GRID_HORIZONTAL);
            } else if (relative_x % CELL_TILE_SIZE == 0) {
                set_tile(x, y, TILE_GRID_VERTICAL);
            }
        }
    }
}

static void draw_board(void)
{
    uint8_t index;
    uint8_t x;
    uint8_t y;

    for (index = 0; index < SIXIES_BOARD_CELLS; ++index) {
        if (game.board[index] == 0) {
            continue;
        }
        x = (uint8_t)(BOARD_LEFT + (index % 5) * CELL_TILE_SIZE + 1);
        y = (uint8_t)(BOARD_TOP + (index / 5) * CELL_TILE_SIZE + 1);
        set_cell_palette(index, palette_for_value(game.board[index]));
        draw_die(x, y, game.board[index], STYLE_NORMAL);
    }
}

static void draw_current_piece(void)
{
    uint8_t origin;
    uint8_t second;
    uint8_t valid;
    uint8_t x;
    uint8_t y;
    uint8_t style;

    if (game.game_over) {
        return;
    }
    valid = sixies_get_placement(&game, &origin, &second);
    style = valid ? STYLE_PREVIEW : STYLE_INVALID;
    x = (uint8_t)(BOARD_LEFT + (origin % 5) * CELL_TILE_SIZE + 1);
    y = (uint8_t)(BOARD_TOP + (origin / 5) * CELL_TILE_SIZE + 1);
    set_cell_palette(origin, valid ? palette_for_value(game.piece_values[0]) : 3);
    draw_die(x, y, game.piece_values[0], style);

    if (game.piece_count == 2 && second != SIXIES_NO_CELL) {
        style = valid ? STYLE_PREVIEW : STYLE_INVALID;
        x = (uint8_t)(BOARD_LEFT + (second % 5) * CELL_TILE_SIZE + 1);
        y = (uint8_t)(BOARD_TOP + (second / 5) * CELL_TILE_SIZE + 1);
        set_cell_palette(second, valid ? palette_for_value(game.piece_values[1]) : 3);
        draw_die(x, y, game.piece_values[1], style);
    }
}

static const char* message_name(uint8_t placement_valid)
{
    if (game.game_over) {
        return "OVER";
    }
    if (shell_message == MESSAGE_BLOCKED || !placement_valid) {
        return "BLOCK";
    }
    if (shell_message == MESSAGE_MERGED) {
        return "MERGE";
    }
    if (shell_message == MESSAGE_NEW_GAME) {
        return "NEW";
    }
    if (shell_message == MESSAGE_UI_TODO) {
        return "UI";
    }
    return "READY";
}

static void draw_sidebar(void)
{
    uint8_t origin;
    uint8_t second;
    uint8_t valid;
    uint8_t style;

    valid = sixies_get_placement(&game, &origin, &second);
    draw_text(26, 5, "NEXT");
    style = STYLE_NORMAL;
    set_attribute_block(NEXT_LEFT, NEXT_TOP, palette_for_value(game.piece_values[0]));
    draw_die(NEXT_LEFT, NEXT_TOP, game.piece_values[0], style);
    if (game.piece_count == 2) {
        style = STYLE_NORMAL;
        set_attribute_block(NEXT_LEFT, NEXT_TOP + 4, palette_for_value(game.piece_values[1]));
        draw_die(NEXT_LEFT, NEXT_TOP + 4, game.piece_values[1], style);
    }
    draw_text(26, 17, game.singles_only ? "SINGLE" : "NORMAL");
    draw_text(26, 20, message_name(valid));
}

static void build_screen(void)
{
    memset(nametable, 0, sizeof(nametable));
    memset(attributes, 0, sizeof(attributes));
    draw_text(1, 1, "SIXIES");
    draw_text(18, 1, "SCORE");
    draw_score(24, 1, game.score);
    draw_grid();
    draw_board();
    draw_current_piece();
    draw_sidebar();
    draw_text(1, 27, "D-PAD MOVE  A PLACE");
    draw_text(1, 29, "B ROTATE  START NEW");
}

static void set_ppu_address(uint16_t address)
{
    (void)PPU.status;
    PPU.vram.address = (uint8_t)(address >> 8);
    PPU.vram.address = (uint8_t)address;
}

static void write_ppu_data(uint16_t address, const uint8_t* data, uint16_t size)
{
    set_ppu_address(address);
    while (size-- != 0) {
        PPU.vram.data = *data++;
    }
}

static void render_screen(void)
{
    build_screen();
    waitvsync();
    PPU.control = 0;
    PPU.mask = 0;
    write_ppu_data(0x2000, nametable, NAMETABLE_SIZE);
    write_ppu_data(0x23c0, attributes, ATTRIBUTE_SIZE);
    write_ppu_data(0x3f00, palette_data, sizeof(palette_data));
    (void)PPU.status;
    PPU.scroll = 0;
    PPU.scroll = 0;
    PPU.control = 0x80;
    PPU.mask = 0x0a;
}

static uint8_t next_seed(void)
{
    uint8_t seed;

    seed = (uint8_t)(game.rng_state ^ frame_counter ^ 0xa5);
    seed |= 1;
    return seed;
}

static void start_new_game(void)
{
    sixies_new_game(&game, next_seed());
    shell_message = MESSAGE_NEW_GAME;
}

static void handle_action(uint8_t action)
{
    uint8_t origin;
    uint8_t second;

    if (action & JOY_START_MASK) {
        start_new_game();
        return;
    }
    if (game.game_over) {
        if (action & JOY_BTN_A_MASK) {
            start_new_game();
        }
        return;
    }

    shell_message = MESSAGE_READY;
    if (action & JOY_UP_MASK) {
        sixies_move_cursor(&game, 0, -1);
    } else if (action & JOY_DOWN_MASK) {
        sixies_move_cursor(&game, 0, 1);
    } else if (action & JOY_LEFT_MASK) {
        sixies_move_cursor(&game, -1, 0);
    } else if (action & JOY_RIGHT_MASK) {
        sixies_move_cursor(&game, 1, 0);
    } else if (action & JOY_BTN_B_MASK) {
        sixies_rotate(&game);
    } else if (action & JOY_BTN_A_MASK) {
        if (sixies_place_current(&game)) {
            shell_message = game.event_count ? MESSAGE_MERGED : MESSAGE_READY;
        } else {
            shell_message = MESSAGE_BLOCKED;
        }
    } else if (action & JOY_SELECT_MASK) {
        shell_message = MESSAGE_UI_TODO;
    }

    if (!sixies_get_placement(&game, &origin, &second) &&
        shell_message == MESSAGE_READY) {
        shell_message = MESSAGE_BLOCKED;
    }
}

int main(void)
{
    uint8_t previous;
    uint8_t buttons;
    uint8_t pressed;
    uint8_t action;

    if (joy_install((void*)joy_static_stddrv) != JOY_ERR_OK) {
        for (;;) {
            waitvsync();
        }
    }

    frame_counter = 0x31;
    repeat_counter = 0;
    sixies_new_game(&game, 0xa5);
    shell_message = MESSAGE_NEW_GAME;
    render_screen();
    previous = joy_read(JOY_1);

    for (;;) {
        waitvsync();
        ++frame_counter;
        buttons = joy_read(JOY_1);
        pressed = (uint8_t)(buttons & (uint8_t)~previous);
        action = pressed;

        if (pressed & DIR_MASK) {
            repeat_counter = 12;
        } else if (buttons & DIR_MASK) {
            if (repeat_counter == 0) {
                action |= (uint8_t)(buttons & DIR_MASK);
                repeat_counter = 4;
            } else {
                --repeat_counter;
            }
        } else {
            repeat_counter = 0;
        }

        previous = buttons;
        if (action != 0) {
            handle_action(action);
            render_screen();
        }
    }
    return 0;
}
