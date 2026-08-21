#include <apple2.h>
#include <conio.h>
#include <fcntl.h>
#include <peekpoke.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "dice_assets.h"
#include "game_over_assets.h"
#include "instructions_assets.h"
#include "merge_effects.h"
#include "presents_assets.h"

#if PRESENTS_AUX_PACKED_BYTES > DICE_BLITS_BYTES \
    || PRESENTS_MAIN_PACKED_BYTES > DICE_BLITS_BYTES \
    || INSTRUCTIONS_AUX_PACKED_BYTES > DICE_BLITS_BYTES \
    || INSTRUCTIONS_MAIN_PACKED_BYTES > DICE_BLITS_BYTES \
    || GAME_OVER_AUX_PACKED_BYTES > DICE_BLITS_BYTES \
    || GAME_OVER_MAIN_PACKED_BYTES > DICE_BLITS_BYTES
#error "packed DHGR bank does not fit the startup dice buffer"
#endif

#define HGR_PAGE ((unsigned char*) 0x2000)
#define TEXT_PAGE ((unsigned char*) 0x0400)

#define EIGHTY_STORE_OFF 0xC000
#define RAMWRT_MAIN 0xC004
#define COL80_OFF 0xC00C
#define COL80_ON 0xC00D
#define GRAPHICS_ON 0xC050
#define TEXT_ON 0xC051
#define FULL_GRAPHICS 0xC052
#define MIXED_GRAPHICS 0xC053
#define PAGE1 0xC054
#define HIRES_ON 0xC057
#define DHIRES_ON 0xC05E
#define DHIRES_OFF 0xC05F
#define VBL_STATUS 0xC019

#define DHGR_BANK_SIZE 8192u
#define DHGR_TRANSFER_SIZE 1024u
#define DHGR_SIGNAL_WIDTH 560u
#define DHGR_SCANLINES 192u

#if DICE_MIN_BLIT_BYTE_COUNT < 2u
#error "DHGR assembly blitters require at least two bytes per bank span"
#endif

#if MERGE_STAR_BYTES > DHGR_TRANSFER_SIZE \
    || MERGE_EFFECT_BANK_BYTES > DHGR_TRANSFER_SIZE \
    || DICE_BLIT_BANK_BYTES > DHGR_TRANSFER_SIZE
#error "generated asset does not fit the shared DHGR transfer buffer"
#endif

#define BOARD_SIZE 5
#define BOARD_CELLS 25
#define CELL_SIZE 24
#define CELL_PITCH_X 29
#define CELL_PITCH_Y 30
#define BOARD_LEFT 69
#define BOARD_TOP 8

#define KEY_CURS_UP 0x0B
#define KEY_CURS_DOWN 0x0A

#define MERGE_EFFECT_AWESOME 0u
#define MERGE_EFFECT_FIVES 3u
#define MERGE_EFFECT_SIXIES 5u
#define SCORE_DIGITS 5u
#define HOVER_FLASH_FRAMES 18u
#define ATTRACT_SCREEN_SECONDS 5u
#define INITIAL_TITLE_SECONDS 10u
#define NTSC_FRAMES_PER_SECOND 60u

static unsigned char board[BOARD_CELLS];
static unsigned char placement_board_before[BOARD_CELLS];
static unsigned char dice_blits[DICE_BLITS_BYTES];
static unsigned char dhgr_grid_active;
static unsigned char cursor_x;
static unsigned char cursor_y;
static unsigned char piece_count;
static unsigned char piece_a;
static unsigned char piece_b;
static unsigned char orientation;
static unsigned char single_mode;
static unsigned char game_over;
static unsigned char merge_effect_index;
static unsigned char merge_effect_x;
static unsigned char merge_effect_y;
static unsigned char turn_merge_count;
static unsigned int displayed_score;
#ifdef MERGE_EFFECT_DEMO
static unsigned char merge_effect_demo_index;
#endif
static unsigned int score;

unsigned char dhgr_transfer_buffer[DHGR_TRANSFER_SIZE];
unsigned char merge_effect_row_low[MERGE_EFFECT_HEIGHT];
unsigned char merge_effect_row_high[MERGE_EFFECT_HEIGHT];
unsigned char merge_effect_byte_offset;
unsigned char* dhgr_blit_source;
unsigned char dhgr_blit_row_index;
unsigned char dhgr_blit_row_end;
unsigned char dhgr_blit_byte_offset;
unsigned char dhgr_blit_byte_count;
unsigned char dhgr_blit_last_byte;
unsigned char dhgr_blit_first_mask;
unsigned char dhgr_blit_last_mask;
unsigned char score_blit_position;
unsigned char score_blit_digit;
const unsigned char* dhgr_first_restore_source;
const unsigned char* dhgr_last_restore_source;
extern void __fastcall__ copy_buffer_to_aux(void* destination);
extern void replace_dhgr_sprite_aux(void);
extern void replace_dhgr_sprite_main(void);
extern void replace_dhgr_opaque_aux(void);
extern void replace_dhgr_opaque_main(void);
extern void clear_dhgr_tile_aux(void);
extern void clear_dhgr_tile_main(void);
extern void invert_dhgr_tile_aux(void);
extern void invert_dhgr_tile_main(void);
extern void run_merge_grid_shake(void);
extern void draw_merge_effect_aux(void);
extern void draw_merge_effect_main(void);
extern void save_merge_effect_background(void);
extern void restore_merge_effect_background(void);
extern void xor_merge_star(void);
extern void xor_score_digit(void);

static void replace_dhgr_source(unsigned char* source, unsigned char col, unsigned char row);
static void redraw_board_cell_at(unsigned char col, unsigned char row);
static void redraw_board_changes(void);
static void wait_animation_frames(unsigned char frames);
static void append_u16(char* buffer, unsigned int value);

static const char merge_effect_files[MERGE_EFFECT_COUNT][5] = {
    "FX00", "FX01", "FX02", "FX03", "FX04",
    "FX05", "FX06", "FX07", "FX08", "FX09",
};

static const unsigned char first_merge_effects[7] = {
    1, 2, 4, 6, 7, 8, 9,
};

static const unsigned char firework_side_x[9] = {0, 2, 4, 6, 8, 10, 12, 14, 16};
static const signed char firework_side_y[9] = {0, -5, -8, -10, -7, -2, 7, 19, 32};
static const signed char firework_center_y[9] = {0, -7, -12, -15, -12, -5, 5, 18, 32};

static const signed char orient_dx[4] = {1, 0, -1, 0};
static const signed char orient_dy[4] = {0, 1, 0, -1};
static const unsigned char hgr_pixel_masks[7] = {1, 2, 4, 8, 16, 32, 64};
static const unsigned char hgr_set_from[7] = {0x7F, 0x7E, 0x7C, 0x78, 0x70, 0x60, 0x40};
static const unsigned char hgr_set_through[7] = {1, 3, 7, 15, 31, 63, 127};
static unsigned char flood_seen[BOARD_CELLS];
static unsigned char flood_list[BOARD_CELLS];

static unsigned hgr_row_address(unsigned y) {
    return 0x2000u + ((y & 0x07u) << 10) + (((y >> 3) & 0x07u) << 7) + ((y >> 6) * 0x28u);
}

#pragma code-name (push, "LC")

static void activate_soft_switch(unsigned address) {
    *((volatile unsigned char*) address) = 0;
}

#pragma code-name (pop)

static void set_graphics(unsigned char mixed) {
    activate_soft_switch(EIGHTY_STORE_OFF);
    activate_soft_switch(RAMWRT_MAIN);
    activate_soft_switch(COL80_OFF);
    activate_soft_switch(DHIRES_OFF);
    activate_soft_switch(GRAPHICS_ON);
    if (mixed) {
        activate_soft_switch(MIXED_GRAPHICS);
    } else {
        activate_soft_switch(FULL_GRAPHICS);
    }
    activate_soft_switch(PAGE1);
    activate_soft_switch(HIRES_ON);
}

static void set_text(void) {
    activate_soft_switch(EIGHTY_STORE_OFF);
    activate_soft_switch(RAMWRT_MAIN);
    activate_soft_switch(COL80_OFF);
    activate_soft_switch(DHIRES_OFF);
    activate_soft_switch(TEXT_ON);
}

static void set_double_hires(unsigned char mixed) {
    activate_soft_switch(EIGHTY_STORE_OFF);
    activate_soft_switch(RAMWRT_MAIN);
    activate_soft_switch(GRAPHICS_ON);
    if (mixed) {
        activate_soft_switch(MIXED_GRAPHICS);
    } else {
        activate_soft_switch(FULL_GRAPHICS);
    }
    activate_soft_switch(PAGE1);
    activate_soft_switch(HIRES_ON);

    /* RGB card mode 11: record 80COL=0 twice, then leave DHGR and 80COL on. */
    activate_soft_switch(COL80_OFF);
    activate_soft_switch(DHIRES_ON);
    activate_soft_switch(DHIRES_OFF);
    activate_soft_switch(DHIRES_ON);
    activate_soft_switch(DHIRES_OFF);
    activate_soft_switch(COL80_ON);
    activate_soft_switch(DHIRES_ON);
}

static void hgr_clear_page(void) {
    memset(HGR_PAGE, 0, 8192);
}

static void hgr_set_pixel(unsigned x, unsigned y) {
    unsigned addr;

    if (x >= 280 || y >= 160) {
        return;
    }
    addr = hgr_row_address(y) + (x / 7u);
    *((unsigned char*) addr) |= hgr_pixel_masks[x % 7u];
}

static void hgr_hline(unsigned x1, unsigned x2, unsigned y) {
    unsigned swap;
    unsigned start_byte;
    unsigned end_byte;
    unsigned column;
    unsigned char first_bit;
    unsigned char last_bit;
    unsigned char* bytes;

    if (y >= 160) {
        return;
    }
    if (x2 < x1) {
        swap = x1;
        x1 = x2;
        x2 = swap;
    }
    if (x1 >= 280) {
        return;
    }
    if (x2 >= 280) {
        x2 = 279;
    }

    start_byte = x1 / 7u;
    end_byte = x2 / 7u;
    first_bit = (unsigned char) (x1 % 7u);
    last_bit = (unsigned char) (x2 % 7u);
    bytes = (unsigned char*) (hgr_row_address(y) + start_byte);

    if (start_byte == end_byte) {
        bytes[0] |= hgr_set_from[first_bit] & hgr_set_through[last_bit];
        return;
    }

    bytes[0] |= hgr_set_from[first_bit];
    for (column = 1; column < end_byte - start_byte; ++column) {
        bytes[column] |= 0x7Fu;
    }
    bytes[end_byte - start_byte] |= hgr_set_through[last_bit];
}

static void hgr_vline(unsigned x, unsigned y1, unsigned y2) {
    unsigned y;
    unsigned swap;
    unsigned byte_offset;
    unsigned char mask;

    if (x >= 280) {
        return;
    }
    if (y2 < y1) {
        swap = y1;
        y1 = y2;
        y2 = swap;
    }
    if (y1 >= 160) {
        return;
    }
    if (y2 >= 160) {
        y2 = 159;
    }

    byte_offset = x / 7u;
    mask = hgr_pixel_masks[x % 7u];
    for (y = y1; y <= y2; ++y) {
        *((unsigned char*) (hgr_row_address(y) + byte_offset)) |= mask;
    }
}

static void hgr_rect(unsigned x, unsigned y, unsigned width, unsigned height) {
    if (width == 0 || height == 0) {
        return;
    }
    hgr_hline(x, x + width - 1u, y);
    hgr_hline(x, x + width - 1u, y + height - 1u);
    hgr_vline(x, y, y + height - 1u);
    hgr_vline(x + width - 1u, y, y + height - 1u);
}

static void hgr_double_rect(unsigned x, unsigned y, unsigned width, unsigned height) {
    hgr_rect(x, y, width, height);
    hgr_rect(x + 1u, y + 1u, width - 2u, height - 2u);
}

static void hgr_draw_x(unsigned x, unsigned y, unsigned width, unsigned height) {
    unsigned step;
    unsigned limit = width < height ? width : height;
    for (step = 0; step < limit; ++step) {
        hgr_set_pixel(x + step, y + step);
        hgr_set_pixel(x + width - 1u - step, y + step);
    }
}

static void hgr_set_pixel_phase(unsigned x, unsigned y, unsigned char shifted) {
    unsigned addr;
    unsigned char* byte;

    if (x >= 280 || y >= 160) {
        return;
    }
    addr = hgr_row_address(y) + (x / 7u);
    byte = (unsigned char*) addr;
    *byte |= hgr_pixel_masks[x % 7u];
    if (shifted) {
        *byte |= 0x80u;
    }
}

static unsigned text_row_offset(unsigned char row) {
    return ((unsigned) (row & 0x07u) << 7) + (unsigned) (row >> 3) * 40u;
}

static unsigned char load_a2fm_screen(const char* filename) {
    int fd;
    int count;
    unsigned char bank;
    unsigned chunk;
    unsigned char* destination;

    activate_soft_switch(EIGHTY_STORE_OFF);
    activate_soft_switch(PAGE1);
    activate_soft_switch(RAMWRT_MAIN);
    fd = open(filename, O_RDONLY);
    if (fd < 0) {
        return 0;
    }

    for (bank = 0; bank < 2; ++bank) {
        destination = HGR_PAGE;
        for (chunk = 0; chunk < DHGR_BANK_SIZE; chunk += DHGR_TRANSFER_SIZE) {
            count = read(fd, dhgr_transfer_buffer, DHGR_TRANSFER_SIZE);
            if (count != DHGR_TRANSFER_SIZE) {
                close(fd);
                return 0;
            }
            if (bank == 0) {
                copy_buffer_to_aux(destination);
            } else {
                memcpy(destination, dhgr_transfer_buffer, DHGR_TRANSFER_SIZE);
            }
            destination += DHGR_TRANSFER_SIZE;
        }
    }

    close(fd);
    return 1;
}

static unsigned char load_dice_blits(void) {
    int fd;
    int count;
    unsigned remaining = DICE_BLITS_BYTES;
    unsigned chunk;
    unsigned checksum = 0;
    unsigned i;
    unsigned char* destination = dice_blits;

    fd = open("DICE.BLITS", O_RDONLY);
    if (fd < 0) {
        return 0;
    }
    while (remaining != 0) {
        chunk = remaining > DHGR_TRANSFER_SIZE ? DHGR_TRANSFER_SIZE : remaining;
        count = read(fd, destination, chunk);
        if (count != chunk) {
            close(fd);
            return 0;
        }
        destination += chunk;
        remaining -= chunk;
    }
    close(fd);
    for (i = 0; i < DICE_BLITS_BYTES; ++i) {
        checksum += dice_blits[i];
    }
    return checksum == DICE_BLITS_CHECKSUM;
}

static unsigned char read_exact(int fd, unsigned char* destination, unsigned count) {
    int received;
    while (count != 0) {
        received = read(fd, destination, count);
        if (received <= 0) {
            return 0;
        }
        destination += received;
        count -= (unsigned) received;
    }
    return 1;
}

#pragma code-name (push, "LC")

static unsigned char unpack_dhgr_page(
    unsigned char* source,
    unsigned char* end,
    unsigned char auxiliary
) {
    unsigned char* cursor = source;
    unsigned char* destination = HGR_PAGE;
    unsigned char token = 0;
    unsigned char pending = 0;
    unsigned char repeat = 0;
    unsigned char value = 0;
    unsigned char chunk;
    unsigned output;

    for (chunk = 0; chunk < DHGR_BANK_SIZE / DHGR_TRANSFER_SIZE; ++chunk) {
        for (output = 0; output < DHGR_TRANSFER_SIZE; ++output) {
            if (pending == 0) {
                if (cursor >= end) {
                    return 0;
                }
                token = *cursor++;
                pending = (unsigned char) ((token & 0x7Fu) + 1u);
                repeat = token & 0x80u;
                if (repeat != 0) {
                    if (cursor >= end) {
                        return 0;
                    }
                    value = *cursor++;
                }
            }
            if (repeat != 0) {
                dhgr_transfer_buffer[output] = value;
            } else {
                if (cursor >= end) {
                    return 0;
                }
                dhgr_transfer_buffer[output] = *cursor++;
            }
            --pending;
        }
        if (auxiliary) {
            copy_buffer_to_aux(destination);
        } else {
            memcpy(destination, dhgr_transfer_buffer, DHGR_TRANSFER_SIZE);
        }
        destination += DHGR_TRANSFER_SIZE;
    }
    if (pending != 0) {
        return 0;
    }
    return cursor == end;
}

static unsigned char load_rle_dhgr_screen(
    const char* filename,
    unsigned auxiliary_bytes,
    unsigned main_bytes,
    unsigned expected_checksum,
    unsigned char mixed
) {
    int fd;
    unsigned i;
    unsigned checksum = 0;

    fd = open(filename, O_RDONLY);
    if (fd < 0) {
        return 0;
    }
    if (!read_exact(fd, dice_blits, auxiliary_bytes)) {
        close(fd);
        return 0;
    }
    for (i = 0; i < auxiliary_bytes; ++i) {
        checksum += dice_blits[i];
    }
    if (!unpack_dhgr_page(dice_blits, dice_blits + auxiliary_bytes, 1)) {
        close(fd);
        return 0;
    }

    if (!read_exact(fd, dice_blits, main_bytes)) {
        close(fd);
        return 0;
    }
    close(fd);
    for (i = 0; i < main_bytes; ++i) {
        checksum += dice_blits[i];
    }
    if (checksum != expected_checksum) {
        return 0;
    }
    if (!unpack_dhgr_page(dice_blits, dice_blits + main_bytes, 0)) {
        return 0;
    }
    set_double_hires(mixed);
    return 1;
}

static void xor_merge_star_at(int x, int y) {
    int screen_y = y + MERGE_STAR_ACTIVE_TOP;
    unsigned signal;
    unsigned char skip = 0;
    unsigned char count = MERGE_STAR_ACTIVE_HEIGHT;
    unsigned char row;
    unsigned address;

    if (x < 0 || x + 24 > 280 || screen_y >= (int) DHGR_SCANLINES) {
        return;
    }
    if (screen_y < 0) {
        skip = (unsigned char) -screen_y;
        if (skip >= count) {
            return;
        }
        screen_y = 0;
        count -= skip;
    }
    if ((unsigned) screen_y + count > DHGR_SCANLINES) {
        count = (unsigned char) (DHGR_SCANLINES - (unsigned) screen_y);
    }

    signal = (unsigned) x * 2u;
    dhgr_blit_source = dhgr_transfer_buffer
        + (signal % 7u) * MERGE_STAR_PHASE_BYTES
        + (unsigned) skip * MERGE_STAR_SEQUENCE_BYTES;
    dhgr_blit_row_end = count;
    dhgr_blit_byte_offset = (unsigned char) ((signal / 7u) / 2u);
    dhgr_blit_first_mask = (unsigned char) ((signal / 7u) & 1u);
    for (row = 0; row < count; ++row) {
        address = hgr_row_address((unsigned) screen_y + row);
        merge_effect_row_low[row] = (unsigned char) address;
        merge_effect_row_high[row] = (unsigned char) (address >> 8);
    }
    xor_merge_star();
}

static void score_value_digits(unsigned int value, unsigned char* digits) {
    digits[0] = 0;
    while (value >= 10000u) {
        value -= 10000u;
        ++digits[0];
    }
    digits[1] = 0;
    while (value >= 1000u) {
        value -= 1000u;
        ++digits[1];
    }
    digits[2] = 0;
    while (value >= 100u) {
        value -= 100u;
        ++digits[2];
    }
    digits[3] = 0;
    while (value >= 10u) {
        value -= 10u;
        ++digits[3];
    }
    digits[4] = (unsigned char) value;
}

static void xor_score_digit_at(unsigned char position, unsigned char digit) {
    score_blit_position = position;
    score_blit_digit = digit;
    xor_score_digit();
}

static void draw_score_value(unsigned int value) {
    unsigned char digits[SCORE_DIGITS];
    unsigned char position;

    score_value_digits(value, digits);
    for (position = 0; position < SCORE_DIGITS; ++position) {
        xor_score_digit_at(position, digits[position]);
    }
}

static void update_score_display(void) {
    unsigned char old_digits[SCORE_DIGITS];
    unsigned char new_digits[SCORE_DIGITS];
    unsigned char position;

    if (displayed_score == score) {
        return;
    }
    score_value_digits(displayed_score, old_digits);
    score_value_digits(score, new_digits);
    for (position = 0; position < SCORE_DIGITS; ++position) {
        if (old_digits[position] == new_digits[position]) {
            continue;
        }
        xor_score_digit_at(position, old_digits[position]);
        xor_score_digit_at(position, new_digits[position]);
    }
    displayed_score = score;
}

static void xor_merge_firework_frame(unsigned char frame, int base_x, int base_y) {
    xor_merge_star_at(base_x, base_y + firework_center_y[frame]);
    if (frame != 0) {
        xor_merge_star_at(
            base_x - firework_side_x[frame],
            base_y + firework_side_y[frame]
        );
        xor_merge_star_at(
            base_x + firework_side_x[frame],
            base_y + firework_side_y[frame]
        );
    }
}

static void run_merge_star_burst(void) {
    int fd;
    int base_x;
    int base_y;
    unsigned char frame;

    fd = open("MERGESTAR", O_RDONLY);
    if (fd < 0) {
        return;
    }
    if (!read_exact(fd, dhgr_transfer_buffer, MERGE_STAR_BYTES)) {
        close(fd);
        return;
    }
    close(fd);
    base_x = BOARD_LEFT + (int) merge_effect_x * CELL_PITCH_X + 1;
    base_y = BOARD_TOP + (int) merge_effect_y * CELL_PITCH_Y;
    for (frame = 0; frame < 9; ++frame) {
        xor_merge_firework_frame(frame, base_x, base_y);
        wait_animation_frames(2);
        xor_merge_firework_frame(frame, base_x, base_y);
    }
}

#pragma code-name (pop)

static unsigned char draw_merge_effect(unsigned char effect) {
    int fd;

    if (effect >= MERGE_EFFECT_COUNT) {
        return 0;
    }
    fd = open(merge_effect_files[effect], O_RDONLY);
    if (fd < 0) {
        return 0;
    }
    if (!read_exact(fd, dhgr_transfer_buffer, MERGE_EFFECT_BANK_BYTES)) {
        close(fd);
        return 0;
    }
    draw_merge_effect_aux();
    if (!read_exact(fd, dhgr_transfer_buffer, MERGE_EFFECT_BANK_BYTES)) {
        close(fd);
        return 0;
    }
    draw_merge_effect_main();
    close(fd);
    return 1;
}

static void dhgr_begin_text(void) {
    memset(TEXT_PAGE, 0xA0, 1024);
    memset(dhgr_transfer_buffer, 0xA0, sizeof(dhgr_transfer_buffer));
}

static void dhgr_add_text_line(unsigned char row, const char* text) {
    unsigned char length = (unsigned char) strlen(text);
    unsigned char column;
    unsigned char screen_column;
    unsigned offset;
    unsigned char code;

    if (row >= 24) {
        return;
    }
    if (length > 80) {
        length = 80;
    }
    screen_column = (unsigned char) ((80u - length) / 2u);
    offset = text_row_offset(row);

    for (column = 0; column < length; ++column) {
        code = (unsigned char) text[column] | 0x80u;
        if (screen_column & 1u) {
            TEXT_PAGE[offset + screen_column / 2u] = code;
        } else {
            dhgr_transfer_buffer[offset + screen_column / 2u] = code;
        }
        ++screen_column;
    }
}

static void dhgr_finish_text(void) {
    copy_buffer_to_aux(TEXT_PAGE);
}

static unsigned char cell_index(unsigned char x, unsigned char y) {
    return (unsigned char) (y * BOARD_SIZE + x);
}

static unsigned char board_value(unsigned char x, unsigned char y) {
    return board[cell_index(x, y)];
}

static void board_set(unsigned char x, unsigned char y, unsigned char value) {
    board[cell_index(x, y)] = value;
}

static unsigned char count_value(unsigned char value) {
    unsigned char i;
    unsigned char count = 0;
    for (i = 0; i < BOARD_CELLS; ++i) {
        if (board[i] == value) {
            ++count;
        }
    }
    return count;
}

static unsigned char has_adjacent_empty_pair(void) {
    unsigned char x;
    unsigned char y;
    for (y = 0; y < BOARD_SIZE; ++y) {
        for (x = 0; x < BOARD_SIZE; ++x) {
            if (board_value(x, y) != 0) {
                continue;
            }
            if (x + 1u < BOARD_SIZE && board_value((unsigned char) (x + 1u), y) == 0) {
                return 1;
            }
            if (y + 1u < BOARD_SIZE && board_value(x, (unsigned char) (y + 1u)) == 0) {
                return 1;
            }
        }
    }
    return 0;
}

static unsigned char has_empty_cell(void) {
    unsigned char i;
    for (i = 0; i < BOARD_CELLS; ++i) {
        if (board[i] == 0) {
            return 1;
        }
    }
    return 0;
}

static unsigned char has_any_placement(void) {
    if (piece_count == 1) {
        return has_empty_cell();
    }
    return has_adjacent_empty_pair();
}

static unsigned char random_face(unsigned char allow_five) {
    unsigned char value;
    if (allow_five && ((rand() & 15) == 0)) {
        return 5;
    }
    value = (unsigned char) ((rand() % 4) + 1);
    return value;
}

static void generate_piece(
    unsigned char* count,
    unsigned char* first,
    unsigned char* second
) {
    unsigned char allow_five;

    allow_five = count_value(5) >= 5;
    if (single_mode) {
        *count = 1;
    } else {
        *count = (rand() & 1) ? 2 : 1;
    }
    *first = random_face(allow_five);
    *second = random_face(allow_five);
    if (*count == 2 && *first == 4 && *second == 4) {
        *second = 3;
    }
}

static void reset_piece_position(void) {
    cursor_x = 2;
    cursor_y = 2;
    orientation = 0;
    game_over = !has_any_placement();
}

static void initialize_piece(void) {
    generate_piece(&piece_count, &piece_a, &piece_b);
    reset_piece_position();
}

static void advance_piece(void) {
    generate_piece(&piece_count, &piece_a, &piece_b);
    reset_piece_position();
}

static void clear_bottom_text(void) {
    unsigned char row;
    for (row = 20; row < 24; ++row) {
        gotoxy(0, row);
        cprintf("                                        ");
    }
}

static void write_bottom_line(unsigned char row, const char* text) {
    gotoxy(0, row);
    cprintf("%-40s", text);
}

static void append_u16(char* buffer, unsigned int value) {
    char temp[6];
    unsigned char pos = 0;
    if (value == 0) {
        buffer[0] = '0';
        buffer[1] = '\0';
        return;
    }
    while (value > 0) {
        temp[pos++] = (char) ('0' + (value % 10u));
        value /= 10u;
    }
    while (pos > 0) {
        *buffer++ = temp[--pos];
    }
    *buffer = '\0';
}

static void status_text(void) {
    char line1[41];
    char line2[41];
    char digits[8];
    unsigned char pos;

    clear_bottom_text();
    strcpy(line1, "SCORE ");
    append_u16(digits, score);
    strcat(line1, digits);
    strcat(line1, single_mode ? "   MODE SINGLE" : "   MODE MIXED");

    strcpy(line2, "CUR ");
    pos = (unsigned char) strlen(line2);
    line2[pos++] = (char) ('0' + piece_a);
    if (piece_count == 2) {
        line2[pos++] = '-';
        line2[pos++] = (char) ('0' + piece_b);
    }
    line2[pos] = '\0';

    write_bottom_line(20, line1);
    write_bottom_line(21, line2);
    if (!game_over) {
        write_bottom_line(22, "ARROWS/WASD MOVE R ROTATE SPACE PLACE");
        write_bottom_line(23, "N STARTS A NEW GAME");
    } else {
        write_bottom_line(22, "GAME OVER  SPACE OR N FOR NEW GAME");
    }
}

static unsigned char die_asset_pixel(
    const unsigned char* mask,
    unsigned char x,
    unsigned char y
) {
    unsigned offset = (unsigned) y * DICE_ASSET_ROW_BYTES + (x >> 3);
    return mask[offset] & (1u << (x & 7u));
}

static void draw_asset_die(
    unsigned x,
    unsigned y,
    const unsigned char* mask,
    unsigned char value
) {
    unsigned char row;
    unsigned char col;
    unsigned char start;
    unsigned char parity = value == 3 || value == 5 || value == 6;
    unsigned char shifted = value == 2 || value == 5 || value == 6;
    unsigned char solid;

    for (row = 0; row < DICE_ASSET_SIZE; ++row) {
        col = 0;
        while (col < DICE_ASSET_SIZE) {
            while (col < DICE_ASSET_SIZE && !die_asset_pixel(mask, col, row)) {
                ++col;
            }
            if (col >= DICE_ASSET_SIZE) {
                break;
            }

            solid = value == 1 || (value == 5 && (row & 1u) != 0);
            if (!solid) {
                while (col < DICE_ASSET_SIZE && die_asset_pixel(mask, col, row)) {
                    if (((x + col) & 1u) == parity) {
                        hgr_set_pixel_phase(x + col, y + row, shifted);
                    }
                    ++col;
                }
            } else {
                start = col;
                while (col < DICE_ASSET_SIZE && die_asset_pixel(mask, col, row)) {
                    ++col;
                }
                hgr_hline(x + start, x + col - 1u, y + row);
            }
        }
    }
}

static const unsigned char* die_face_mask(unsigned char value) {
    switch (value) {
        case 1: return die_one_face_mask;
        case 2: return die_two_face_mask;
        case 3: return die_three_face_mask;
        case 4: return die_four_face_mask;
        case 5: return die_five_face_mask;
        case 6: return die_six_face_mask;
    }
    return die_one_face_mask;
}

static void replace_dhgr_source(unsigned char* source, unsigned char col, unsigned char row) {
    unsigned char restore_index = (unsigned char) (col * BOARD_SIZE + row);

    dhgr_blit_source = source;
    dhgr_blit_row_index = (unsigned char) ((unsigned) row * DICE_BLIT_ROWS);
    dhgr_blit_row_end = (unsigned char) (dhgr_blit_row_index + DICE_BLIT_ROWS);
    dhgr_blit_byte_offset = dice_aux_byte_offsets[col];
    dhgr_blit_byte_count = dice_aux_byte_counts[col];
    dhgr_blit_last_byte = (unsigned char) (dhgr_blit_byte_count - 1u);
    dhgr_blit_first_mask = dice_aux_first_masks[col];
    dhgr_blit_last_mask = dice_aux_last_masks[col];
    dhgr_first_restore_source = dice_edge_restore_pool
        + dice_aux_first_restore_offsets[restore_index];
    dhgr_last_restore_source = dice_edge_restore_pool
        + dice_aux_last_restore_offsets[restore_index];
    replace_dhgr_sprite_aux();

    dhgr_blit_source = source + DICE_BLIT_BANK_BYTES;
    dhgr_blit_byte_offset = dice_main_byte_offsets[col];
    dhgr_blit_byte_count = dice_main_byte_counts[col];
    dhgr_blit_last_byte = (unsigned char) (dhgr_blit_byte_count - 1u);
    dhgr_blit_first_mask = dice_main_first_masks[col];
    dhgr_blit_last_mask = dice_main_last_masks[col];
    dhgr_first_restore_source = dice_edge_restore_pool
        + dice_main_first_restore_offsets[restore_index];
    dhgr_last_restore_source = dice_edge_restore_pool
        + dice_main_last_restore_offsets[restore_index];
    replace_dhgr_sprite_main();
}

static void replace_dhgr_asset(unsigned offset, unsigned char col, unsigned char row) {
    replace_dhgr_source(dice_blits + offset, col, row);
}

static void draw_die(unsigned char col, unsigned char row, unsigned char value, unsigned char emph) {
    unsigned x;
    unsigned y;

    if (dhgr_grid_active) {
        replace_dhgr_asset(
            dice_face_blit_offsets[(unsigned char) ((value - 1u) * BOARD_SIZE + col)],
            col,
            row
        );
        return;
    }
    x = BOARD_LEFT + (unsigned) col * CELL_PITCH_X;
    y = BOARD_TOP + (unsigned) row * CELL_PITCH_Y;
    draw_asset_die(x, y, die_face_mask(value), value);
    if (emph) {
        hgr_rect(x - 2u, y - 2u, CELL_SIZE + 4u, CELL_SIZE + 4u);
    }
}

static void draw_sidebar_die(unsigned char row, unsigned char value) {
    unsigned offset = 0;

    dhgr_blit_row_index = (unsigned char) ((unsigned) row * DICE_BLIT_ROWS);
    dhgr_blit_row_end = (unsigned char) (dhgr_blit_row_index + DICE_BLIT_ROWS);
    if (value != 0) {
        offset = dice_face_blit_offsets[
            (unsigned char) ((value - 1u) * BOARD_SIZE + DICE_SIDEBAR_SOURCE_COLUMN)
        ];
        dhgr_blit_source = dice_blits + offset;
    } else {
        dhgr_blit_source = dhgr_transfer_buffer;
    }
    dhgr_blit_byte_offset = DICE_SIDEBAR_AUX_BYTE_OFFSET;
    dhgr_blit_byte_count = DICE_SIDEBAR_AUX_BYTE_COUNT;
    dhgr_blit_last_byte = DICE_SIDEBAR_AUX_BYTE_COUNT - 1u;
    dhgr_blit_first_mask = dice_aux_first_masks[DICE_SIDEBAR_SOURCE_COLUMN];
    dhgr_blit_last_mask = dice_aux_last_masks[DICE_SIDEBAR_SOURCE_COLUMN];
    replace_dhgr_opaque_aux();

    if (value != 0) {
        dhgr_blit_source = dice_blits + offset + DICE_BLIT_BANK_BYTES;
    }
    dhgr_blit_byte_offset = DICE_SIDEBAR_MAIN_BYTE_OFFSET;
    dhgr_blit_byte_count = DICE_SIDEBAR_MAIN_BYTE_COUNT;
    dhgr_blit_last_byte = DICE_SIDEBAR_MAIN_BYTE_COUNT - 1u;
    dhgr_blit_first_mask = dice_main_first_masks[DICE_SIDEBAR_SOURCE_COLUMN];
    dhgr_blit_last_mask = dice_main_last_masks[DICE_SIDEBAR_SOURCE_COLUMN];
    replace_dhgr_opaque_main();
}

static void draw_piece_sidebar(void) {
    memset(dhgr_transfer_buffer, 0, DICE_BLIT_BANK_BYTES);
    draw_sidebar_die(0, piece_a);
    draw_sidebar_die(1, piece_count == 2 ? piece_b : 0);
    set_double_hires(0);
}

static void draw_invalid_mark(unsigned char col, unsigned char row) {
    unsigned x;
    unsigned y;

    if (dhgr_grid_active) {
        replace_dhgr_asset(dice_invalid_blit_offsets[col], col, row);
    } else {
        x = BOARD_LEFT + (unsigned) col * CELL_PITCH_X;
        y = BOARD_TOP + (unsigned) row * CELL_PITCH_Y;
        hgr_draw_x(x + 4u, y + 4u, CELL_SIZE - 8u, CELL_SIZE - 8u);
    }
}

static void draw_board_frame(void) {
    unsigned char row;
    unsigned char col;
    unsigned x;
    unsigned y;

    for (row = 0; row < BOARD_SIZE; ++row) {
        for (col = 0; col < BOARD_SIZE; ++col) {
            x = BOARD_LEFT + (unsigned) col * CELL_PITCH_X;
            y = BOARD_TOP + (unsigned) row * CELL_PITCH_Y;
            hgr_double_rect(x, y, CELL_SIZE, CELL_SIZE);
        }
    }
}

static unsigned char placement_cells(unsigned char* x1, unsigned char* y1, unsigned char* x2, unsigned char* y2) {
    signed char dx;
    signed char dy;
    signed char tx;
    signed char ty;

    *x1 = cursor_x;
    *y1 = cursor_y;
    *x2 = BOARD_SIZE;
    *y2 = BOARD_SIZE;
    if (piece_count == 1) {
        return board_value(*x1, *y1) == 0;
    }

    dx = orient_dx[orientation & 3u];
    dy = orient_dy[orientation & 3u];
    tx = (signed char) cursor_x + dx;
    ty = (signed char) cursor_y + dy;
    if (tx < 0 || ty < 0 || tx >= BOARD_SIZE || ty >= BOARD_SIZE) {
        return 0;
    }

    *x2 = (unsigned char) tx;
    *y2 = (unsigned char) ty;
    if (board_value(*x1, *y1) != 0 || board_value(*x2, *y2) != 0) {
        return 0;
    }
    return 1;
}

static void draw_current_piece_preview(void) {
    unsigned char x1 = 0;
    unsigned char y1 = 0;
    unsigned char x2 = 0;
    unsigned char y2 = 0;

    placement_cells(&x1, &y1, &x2, &y2);
    if (board_value(x1, y1) == 0) {
        draw_die(x1, y1, piece_a, 1);
    } else {
        draw_invalid_mark(x1, y1);
    }

    if (piece_count == 2) {
        if (x2 < BOARD_SIZE && y2 < BOARD_SIZE) {
            if (board_value(x2, y2) == 0) {
                draw_die(x2, y2, piece_b, 1);
            } else {
                draw_invalid_mark(x2, y2);
            }
        }
    }
}

static void clear_hgr_board_tile(unsigned char col, unsigned char row) {
    unsigned y = BOARD_TOP - 2u + (unsigned) row * CELL_PITCH_Y;
    unsigned x = BOARD_LEFT - 2u + (unsigned) col * CELL_PITCH_X;
    unsigned char line;
    unsigned char pixel;
    unsigned char* byte;

    for (line = 0; line < CELL_SIZE + 4u; ++line) {
        for (pixel = 0; pixel < CELL_SIZE + 4u; ++pixel) {
            byte = (unsigned char*) (hgr_row_address(y + line) + (x + pixel) / 7u);
            *byte &= (unsigned char) ~hgr_pixel_masks[(x + pixel) % 7u];
        }
    }
}

static void clear_dhgr_board_tile(unsigned char col, unsigned char row) {
    unsigned char restore_index = (unsigned char) (col * BOARD_SIZE + row);

    dhgr_blit_row_index = (unsigned char) ((unsigned) row * DICE_BLIT_ROWS);
    dhgr_blit_row_end = (unsigned char) (dhgr_blit_row_index + DICE_BLIT_ROWS);
    dhgr_blit_byte_offset = dice_aux_byte_offsets[col];
    dhgr_blit_byte_count = dice_aux_byte_counts[col];
    dhgr_blit_last_byte = (unsigned char) (dhgr_blit_byte_count - 1u);
    dhgr_first_restore_source = dice_edge_restore_pool
        + dice_aux_first_restore_offsets[restore_index];
    dhgr_last_restore_source = dice_edge_restore_pool
        + dice_aux_last_restore_offsets[restore_index];
    clear_dhgr_tile_aux();

    dhgr_blit_byte_offset = dice_main_byte_offsets[col];
    dhgr_blit_byte_count = dice_main_byte_counts[col];
    dhgr_blit_last_byte = (unsigned char) (dhgr_blit_byte_count - 1u);
    dhgr_first_restore_source = dice_edge_restore_pool
        + dice_main_first_restore_offsets[restore_index];
    dhgr_last_restore_source = dice_edge_restore_pool
        + dice_main_last_restore_offsets[restore_index];
    clear_dhgr_tile_main();
}

static void invert_dhgr_board_tile(unsigned char col, unsigned char row) {
    dhgr_blit_row_index = (unsigned char) ((unsigned) row * DICE_BLIT_ROWS);
    dhgr_blit_row_end = (unsigned char) (dhgr_blit_row_index + DICE_BLIT_ROWS);
    dhgr_blit_byte_offset = dice_aux_byte_offsets[col];
    dhgr_blit_byte_count = dice_aux_byte_counts[col];
    dhgr_blit_last_byte = (unsigned char) (dhgr_blit_byte_count - 1u);
    dhgr_blit_first_mask = dice_aux_first_masks[col];
    dhgr_blit_last_mask = dice_aux_last_masks[col];
    invert_dhgr_tile_aux();

    dhgr_blit_byte_offset = dice_main_byte_offsets[col];
    dhgr_blit_byte_count = dice_main_byte_counts[col];
    dhgr_blit_last_byte = (unsigned char) (dhgr_blit_byte_count - 1u);
    dhgr_blit_first_mask = dice_main_first_masks[col];
    dhgr_blit_last_mask = dice_main_last_masks[col];
    invert_dhgr_tile_main();
}

static void redraw_board_cell_at(unsigned char col, unsigned char row) {
    unsigned char value = board_value(col, row);
    unsigned x;
    unsigned y;

    if (dhgr_grid_active) {
        if (value != 0) {
            draw_die(col, row, value, 0);
            return;
        }
        clear_dhgr_board_tile(col, row);
    } else {
        x = BOARD_LEFT + (unsigned) col * CELL_PITCH_X;
        y = BOARD_TOP + (unsigned) row * CELL_PITCH_Y;
        clear_hgr_board_tile(col, row);
        hgr_double_rect(x, y, CELL_SIZE, CELL_SIZE);
    }
    if (value != 0) {
        draw_die(col, row, value, 0);
    }
}

static void add_dirty_cell(
    unsigned char* dirty_x,
    unsigned char* dirty_y,
    unsigned char* dirty_count,
    signed char x,
    signed char y
) {
    unsigned char i;

    if (x < 0 || y < 0 || x >= BOARD_SIZE || y >= BOARD_SIZE) {
        return;
    }
    for (i = 0; i < *dirty_count; ++i) {
        if (dirty_x[i] == (unsigned char) x && dirty_y[i] == (unsigned char) y) {
            return;
        }
    }
    dirty_x[*dirty_count] = (unsigned char) x;
    dirty_y[*dirty_count] = (unsigned char) y;
    ++*dirty_count;
}

static void add_preview_dirty_cells(
    unsigned char* dirty_x,
    unsigned char* dirty_y,
    unsigned char* dirty_count,
    unsigned char position_x,
    unsigned char position_y,
    unsigned char piece_orientation,
    unsigned char preview_piece_count
) {
    add_dirty_cell(dirty_x, dirty_y, dirty_count, position_x, position_y);
    if (preview_piece_count == 1) {
        return;
    }
    add_dirty_cell(
        dirty_x,
        dirty_y,
        dirty_count,
        (signed char) position_x + orient_dx[piece_orientation & 3u],
        (signed char) position_y + orient_dy[piece_orientation & 3u]
    );
}

static void redraw_preview_transition(
    unsigned char old_x,
    unsigned char old_y,
    unsigned char old_orientation
) {
    unsigned char dirty_x[4];
    unsigned char dirty_y[4];
    unsigned char dirty_count = 0;
    unsigned char i;

    add_preview_dirty_cells(dirty_x, dirty_y, &dirty_count, old_x, old_y, old_orientation, piece_count);
    add_preview_dirty_cells(dirty_x, dirty_y, &dirty_count, cursor_x, cursor_y, orientation, piece_count);
    for (i = 0; i < dirty_count; ++i) {
        redraw_board_cell_at(dirty_x[i], dirty_y[i]);
    }
    draw_current_piece_preview();
}

static void invert_current_piece_preview(void) {
    unsigned char x1 = 0;
    unsigned char y1 = 0;
    unsigned char x2 = 0;
    unsigned char y2 = 0;

    if (dhgr_grid_active) {
        placement_cells(&x1, &y1, &x2, &y2);
        invert_dhgr_board_tile(x1, y1);
        if (piece_count == 2 && x2 < BOARD_SIZE && y2 < BOARD_SIZE) {
            invert_dhgr_board_tile(x2, y2);
        }
    }
}

static void render_game(void) {
    unsigned char row;
    unsigned char col;
    unsigned value;

    dhgr_grid_active = load_dice_blits() && load_a2fm_screen("GRID.A2FM");
    if (!dhgr_grid_active) {
        set_graphics(1);
        hgr_clear_page();
        draw_board_frame();
    } else {
        set_double_hires(0);
    }

    for (row = 0; row < BOARD_SIZE; ++row) {
        for (col = 0; col < BOARD_SIZE; ++col) {
            value = board_value(col, row);
            if (value == 0) {
                continue;
            }
            draw_die(col, row, (unsigned char) value, 0);
        }
    }

    if (!game_over) {
        draw_current_piece_preview();
    }
    if (dhgr_grid_active) {
        draw_score_value(displayed_score);
        draw_piece_sidebar();
    }
    if (!dhgr_grid_active) {
        status_text();
    }
}

static void drain_pending_input(void) {
    while (kbhit()) {
        cgetc();
    }
}

static void wait_animation_frames(unsigned char frames) {
    while (frames-- != 0) {
        while ((PEEK(VBL_STATUS) & 0x80u) == 0) {
        }
        while ((PEEK(VBL_STATUS) & 0x80u) != 0) {
        }
    }
}

static void wait_merge_flash(void) {
#ifdef MERGE_EFFECT_DEMO
    wait_animation_frames(120);
#else
    wait_animation_frames(24);
#endif
}

static void toggle_ripple_step(
    unsigned char merge_x,
    unsigned char merge_y,
    unsigned char step
) {
    unsigned char left = step < merge_x ? step : merge_x;
    unsigned char right = BOARD_SIZE - 1u - step;
    unsigned char top = step < merge_y ? step : merge_y;
    unsigned char bottom = BOARD_SIZE - 1u - step;
    unsigned char target_in_row;

    right = right > merge_x ? right : merge_x;
    bottom = bottom > merge_y ? bottom : merge_y;
    invert_dhgr_board_tile(left, merge_y);
    if (right != left) {
        invert_dhgr_board_tile(right, merge_y);
    }
    target_in_row = left == merge_x || right == merge_x;
    if (top != merge_y || !target_in_row) {
        invert_dhgr_board_tile(merge_x, top);
    }
    if (bottom != top && (bottom != merge_y || !target_in_row)) {
        invert_dhgr_board_tile(merge_x, bottom);
    }
}

static void run_merge_grid_ripple(unsigned char merge_x, unsigned char merge_y) {
    unsigned char step;

    for (step = 0; step < BOARD_SIZE; ++step) {
        toggle_ripple_step(merge_x, merge_y, step);
        wait_animation_frames(2);
        toggle_ripple_step(merge_x, merge_y, step);
    }
    set_double_hires(0);
}

static void prepare_merge_effect_position(void) {
    unsigned cell_left = (BOARD_LEFT + merge_effect_x * CELL_PITCH_X) * 2u;
    unsigned cell_top = BOARD_TOP + merge_effect_y * CELL_PITCH_Y;
    unsigned cell_center_x = cell_left + CELL_SIZE;
    unsigned cell_center_y = cell_top + CELL_SIZE / 2u;
    unsigned left = cell_center_x < DHGR_SIGNAL_WIDTH / 2u
        ? DHGR_SIGNAL_WIDTH - MERGE_EFFECT_WIDTH
        : 0u;
    unsigned top = cell_center_y < DHGR_SCANLINES / 2u
        ? DHGR_SCANLINES - MERGE_EFFECT_HEIGHT
        : 0u;
    unsigned row;
    unsigned address;

    merge_effect_byte_offset = (unsigned char) (left / 14u);
    for (row = 0; row < MERGE_EFFECT_HEIGHT; ++row) {
        address = hgr_row_address(top + row);
        merge_effect_row_low[row] = (unsigned char) address;
        merge_effect_row_high[row] = (unsigned char) (address >> 8);
    }
}

static unsigned char show_merge_flash(unsigned char effect) {
    if (effect >= MERGE_EFFECT_COUNT) {
        return 0;
    }
    run_merge_star_burst();
    prepare_merge_effect_position();
    save_merge_effect_background();
    if (!draw_merge_effect(effect)) {
        restore_merge_effect_background();
        return 0;
    }
    wait_merge_flash();
    restore_merge_effect_background();
    drain_pending_input();
    return 1;
}

static unsigned char flood_from(unsigned char start_x, unsigned char start_y, unsigned char value) {
    unsigned char head = 0;
    unsigned char tail = 0;
    unsigned char x;
    unsigned char y;
    unsigned char idx;
    signed char nx;
    signed char ny;
    unsigned char nidx;

    memset(flood_seen, 0, sizeof(flood_seen));
    idx = cell_index(start_x, start_y);
    flood_seen[idx] = 1;
    flood_list[tail++] = idx;

    while (head < tail) {
        idx = flood_list[head++];
        x = (unsigned char) (idx % BOARD_SIZE);
        y = (unsigned char) (idx / BOARD_SIZE);

        nx = (signed char) x - 1;
        ny = (signed char) y;
        if (nx >= 0) {
            nidx = cell_index((unsigned char) nx, (unsigned char) ny);
            if (!flood_seen[nidx] && board[nidx] == value) {
                flood_seen[nidx] = 1;
                flood_list[tail++] = nidx;
            }
        }

        nx = (signed char) x + 1;
        if (nx < BOARD_SIZE) {
            nidx = cell_index((unsigned char) nx, y);
            if (!flood_seen[nidx] && board[nidx] == value) {
                flood_seen[nidx] = 1;
                flood_list[tail++] = nidx;
            }
        }

        ny = (signed char) y - 1;
        if (ny >= 0) {
            nidx = cell_index(x, (unsigned char) ny);
            if (!flood_seen[nidx] && board[nidx] == value) {
                flood_seen[nidx] = 1;
                flood_list[tail++] = nidx;
            }
        }

        ny = (signed char) y + 1;
        if (ny < BOARD_SIZE) {
            nidx = cell_index(x, (unsigned char) ny);
            if (!flood_seen[nidx] && board[nidx] == value) {
                flood_seen[nidx] = 1;
                flood_list[tail++] = nidx;
            }
        }
    }

    return tail;
}

static unsigned char merge_at(unsigned char x, unsigned char y) {
    unsigned char value;
    unsigned char count;
    unsigned char i;
    unsigned char keep;
    unsigned int points;

    value = board_value(x, y);
    if (value == 0) {
        return 0;
    }

    count = flood_from(x, y, value);
    if (count < 3) {
        return 0;
    }

    points = (unsigned int) value * count;
    if (value == 6) {
        points += 50u;
    }
    score += points;
    if (value == 4) {
        merge_effect_index = MERGE_EFFECT_FIVES;
    } else if (value == 5) {
        merge_effect_index = MERGE_EFFECT_SIXIES;
    } else if (turn_merge_count != 0) {
        merge_effect_index = MERGE_EFFECT_AWESOME;
    } else {
        merge_effect_index = first_merge_effects[rand() % 7u];
    }
    turn_merge_count = count == 3u ? value : 1u;
    merge_effect_x = x;
    merge_effect_y = y;
    keep = cell_index(x, y);
    for (i = 0; i < count; ++i) {
        board[flood_list[i]] = 0;
    }
    if (value < 6) {
        board[keep] = (unsigned char) (value + 1u);
    }
    return 1;
}

static void resolve_at(unsigned char x, unsigned char y) {
    while (board_value(x, y) != 0) {
        memcpy(placement_board_before, board, sizeof(board));
        if (!merge_at(x, y)) {
            break;
        }
        redraw_board_changes();
        if (dhgr_grid_active) {
            if (turn_merge_count >= 5u) {
                run_merge_grid_shake();
            }
            run_merge_grid_ripple(merge_effect_x, merge_effect_y);
            update_score_display();
            show_merge_flash(merge_effect_index);
        } else {
            status_text();
        }
    }
}

static void resolve_merges(unsigned char first_x, unsigned char first_y, unsigned char second_x, unsigned char second_y) {
    turn_merge_count = 0;
    resolve_at(first_x, first_y);
    if (piece_count == 2 && board_value(second_x, second_y) != 0) {
        resolve_at(second_x, second_y);
    }
}

static void begin_new_game(void) {
    memset(board, 0, sizeof(board));
    cursor_x = 2;
    cursor_y = 2;
    orientation = 0;
    score = 0;
    displayed_score = 0;
    single_mode = 0;
    game_over = 0;
    initialize_piece();
    render_game();
    drain_pending_input();
}

static unsigned char place_piece(
    unsigned char* x1,
    unsigned char* y1,
    unsigned char* x2,
    unsigned char* y2
) {
    if (!placement_cells(x1, y1, x2, y2)) {
        return 0;
    }

    board_set(*x1, *y1, piece_a);
    if (piece_count == 2) {
        board_set(*x2, *y2, piece_b);
    }
    return 1;
}

static void redraw_board_changes(void) {
    unsigned char row;
    unsigned char col;
    unsigned char cell;

    for (row = 0; row < BOARD_SIZE; ++row) {
        for (col = 0; col < BOARD_SIZE; ++col) {
            cell = cell_index(col, row);
            if (placement_board_before[cell] != board[cell]) {
                redraw_board_cell_at(col, row);
            }
        }
    }
}

static char read_input(void) {
    char ch = cgetc();
    if (ch >= 'a' && ch <= 'z') {
        ch = (char) (ch - ('a' - 'A'));
    }
    return ch;
}

static char wait_for_game_input(void) {
    unsigned char frames = 0;
    unsigned char preview_inverted = 0;

    while (!kbhit()) {
        wait_animation_frames(1);
        ++frames;
        if (frames == HOVER_FLASH_FRAMES) {
            invert_current_piece_preview();
            preview_inverted = (unsigned char) !preview_inverted;
            frames = 0;
        }
    }
    if (preview_inverted) {
        invert_current_piece_preview();
    }
    return read_input();
}

static unsigned char wait_for_start_or_timeout(unsigned frames) {
    char ch;

    while (frames != 0) {
        if (kbhit()) {
            ch = read_input();
            if (ch == ' ' || ch == CH_ENTER || ch == 'N') {
                return 1;
            }
        }
        wait_animation_frames(1);
        --frames;
    }
    return 0;
}

static void presents_screen(void) {
    set_text();
    clrscr();
    if (!load_rle_dhgr_screen(
        "PRESENTS.RLE",
        PRESENTS_AUX_PACKED_BYTES,
        PRESENTS_MAIN_PACKED_BYTES,
        PRESENTS_PACKED_CHECKSUM,
        0
    )) {
        clrscr();
        gotoxy(11, 10);
        cprintf("STUDIO313 PRESENTS");
    }
}

static void title_screen(void) {
    set_text();
    clrscr();
    if (!load_a2fm_screen("TITLE.A2FM")) {
        clrscr();
        gotoxy(10, 8);
        cprintf("SIXIES FOR APPLE II");
        gotoxy(8, 10);
        cprintf("DHGR TITLE FILES NOT FOUND");
        write_bottom_line(22, "SPACE OR RETURN STARTS");
        write_bottom_line(23, "N ALSO STARTS A NEW GAME");
    } else {
        set_double_hires(0);
    }
}

static void instructions_screen(void) {
    set_text();
    clrscr();
    if (!load_rle_dhgr_screen(
        "INSTRUCT.RLE",
        INSTRUCTIONS_AUX_PACKED_BYTES,
        INSTRUCTIONS_MAIN_PACKED_BYTES,
        INSTRUCTIONS_PACKED_CHECKSUM,
        0
    )) {
        clrscr();
        gotoxy(14, 5);
        cprintf("HOW TO PLAY");
        gotoxy(3, 8);
        cprintf("MATCH 3 TOUCHING DICE TO MERGE");
        gotoxy(3, 10);
        cprintf("WASD MOVE  Q OR R ROTATE");
        gotoxy(3, 12);
        cprintf("SPACE OR RETURN PLACES DICE");
        write_bottom_line(20, "SPACE OR RETURN STARTS");
    }
}

static void startup_attract_loop(void) {
    presents_screen();
    if (wait_for_start_or_timeout(
        ATTRACT_SCREEN_SECONDS * NTSC_FRAMES_PER_SECOND
    )) {
        goto start_game;
    }

    title_screen();
    if (wait_for_start_or_timeout(
        INITIAL_TITLE_SECONDS * NTSC_FRAMES_PER_SECOND
    )) {
        goto start_game;
    }

    while (1) {
        instructions_screen();
        if (wait_for_start_or_timeout(
            ATTRACT_SCREEN_SECONDS * NTSC_FRAMES_PER_SECOND
        )) {
            break;
        }

        presents_screen();
        if (wait_for_start_or_timeout(
            ATTRACT_SCREEN_SECONDS * NTSC_FRAMES_PER_SECOND
        )) {
            break;
        }

        title_screen();
        if (wait_for_start_or_timeout(
            ATTRACT_SCREEN_SECONDS * NTSC_FRAMES_PER_SECOND
        )) {
            break;
        }
    }

start_game:
    set_text();
    clrscr();
    drain_pending_input();
}

static void show_game_over(void) {
    char score_line[41];
    char digits[8];
    char ch;

    append_u16(digits, score);
    strcpy(score_line, "FINAL SCORE ");
    strcat(score_line, digits);

    set_text();
    clrscr();
    if (load_rle_dhgr_screen(
        "GAMEOVER.RLE",
        GAME_OVER_AUX_PACKED_BYTES,
        GAME_OVER_MAIN_PACKED_BYTES,
        GAME_OVER_PACKED_CHECKSUM,
        1
    )) {
        dhgr_begin_text();
        dhgr_add_text_line(20, score_line);
        dhgr_add_text_line(21, "SPACE RETURN OR N STARTS A NEW GAME");
        dhgr_add_text_line(22, "APPLE II DHGR ART REBUILT FROM SOURCE PNGS");
        dhgr_add_text_line(23, "READY FOR ANOTHER ROUND");
        dhgr_finish_text();
    } else {
        clrscr();
        gotoxy(15, 8);
        cprintf("GAME OVER");
        write_bottom_line(20, score_line);
        write_bottom_line(21, "SPACE RETURN OR N STARTS A NEW GAME");
        write_bottom_line(22, "DHGR GAME OVER FILES NOT FOUND");
    }

    while (1) {
        ch = read_input();
        if (ch == ' ' || ch == 'N' || ch == CH_ENTER) {
            break;
        }
    }
}

static void game_loop(void) {
    char ch;
    unsigned char old_x;
    unsigned char old_y;
    unsigned char old_orientation;
    unsigned char preview_changed;
    unsigned char placement_changed;
    unsigned char placed_x1;
    unsigned char placed_y1;
    unsigned char placed_x2;
    unsigned char placed_y2;

    while (!game_over) {
        ch = wait_for_game_input();
        old_x = cursor_x;
        old_y = cursor_y;
        old_orientation = orientation;
        preview_changed = 0;
        placement_changed = 0;
        switch (ch) {
#ifdef MERGE_EFFECT_DEMO
            case 'B':
                merge_effect_demo_index = MERGE_EFFECT_SIXIES;
                /* Fall through to exercise the six-removal score in one pass. */
            case 'E':
                merge_effect_x = cursor_x;
                merge_effect_y = cursor_y;
                score += merge_effect_demo_index == MERGE_EFFECT_SIXIES
                    ? 68u
                    : (merge_effect_demo_index == MERGE_EFFECT_FIVES ? 15u : 3u);
                run_merge_grid_ripple(merge_effect_x, merge_effect_y);
                update_score_display();
                show_merge_flash(merge_effect_demo_index);
                merge_effect_demo_index = (unsigned char) (
                    (merge_effect_demo_index + 1u) % MERGE_EFFECT_COUNT
                );
                continue;
#endif
            case 'A':
            case CH_CURS_LEFT:
                if (cursor_x > 0) {
                    --cursor_x;
                    preview_changed = 1;
                }
                break;
            case 'D':
            case CH_CURS_RIGHT:
                if (cursor_x + 1u < BOARD_SIZE) {
                    ++cursor_x;
                    preview_changed = 1;
                }
                break;
            case 'W':
            case KEY_CURS_UP:
                if (cursor_y > 0) {
                    --cursor_y;
                    preview_changed = 1;
                }
                break;
            case 'S':
            case KEY_CURS_DOWN:
                if (cursor_y + 1u < BOARD_SIZE) {
                    ++cursor_y;
                    preview_changed = 1;
                }
                break;
            case 'R':
            case 'Q':
                if (piece_count == 2) {
                    orientation = (unsigned char) ((orientation + 1u) & 3u);
                    preview_changed = 1;
                }
                break;
            case ' ':
            case CH_ENTER:
                memcpy(placement_board_before, board, sizeof(board));
                placement_changed = place_piece(
                    &placed_x1,
                    &placed_y1,
                    &placed_x2,
                    &placed_y2
                );
                break;
            case 'N':
#ifdef SCREEN_SHAKE_DEMO
                run_merge_grid_shake();
#else
                begin_new_game();
#endif
                continue;
        }
        if (placement_changed) {
            redraw_board_changes();
            resolve_merges(placed_x1, placed_y1, placed_x2, placed_y2);
            if (!single_mode && !has_adjacent_empty_pair()) {
                single_mode = 1;
            }
            advance_piece();
            if (!game_over) {
                draw_current_piece_preview();
            }
            if (dhgr_grid_active) {
                draw_piece_sidebar();
            } else {
                status_text();
            }
        } else if (preview_changed) {
            redraw_preview_transition(old_x, old_y, old_orientation);
        }
    }
}

void main(void) {
    srand((unsigned) PEEK(0x4E) | ((unsigned) PEEK(0x4F) << 8));
    set_text();

    startup_attract_loop();
    while (1) {
        begin_new_game();
        game_loop();
        show_game_over();
    }
}
