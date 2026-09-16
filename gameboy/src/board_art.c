#pragma bank 7
#include <gb/gb.h>
#include <stdint.h>
#include <string.h>

#include "generated_art.h"

static uint8_t board_pixels[ART_BOARD_TILES * 16u];
static const uint8_t row_masks[2][3] = {
    {0xFFu, 0xFFu, 0xF0u},
    {0x0Fu, 0xFFu, 0xFFu},
};

void art_reset_board(void) BANKED {
    memset(board_pixels, 0, sizeof(board_pixels));
    set_bkg_data(ART_BOARD_BASE, ART_BOARD_TILES, board_pixels);
}

void art_shift_board(uint8_t shifted) BANKED {
    uint8_t tile_row;
    uint8_t column;
    uint8_t byte;
    uint8_t row_pixels[ART_BOARD_TILE_WIDTH * 16u];
    const uint8_t *source;

    if (!shifted) {
        set_bkg_data(ART_BOARD_BASE, ART_BOARD_TILES, board_pixels);
        return;
    }
    for (tile_row = 0u; tile_row < ART_BOARD_TILE_WIDTH; ++tile_row) {
        source = board_pixels + (uint16_t)tile_row * ART_BOARD_TILE_WIDTH * 16u;
        for (column = 0u; column < ART_BOARD_TILE_WIDTH; ++column) {
            for (byte = 0u; byte < 16u; ++byte) {
                row_pixels[column * 16u + byte] = source[byte] >> 2;
                if (column) row_pixels[column * 16u + byte] |= source[byte - 16] << 6;
            }
            source += 16u;
        }
        set_bkg_data(ART_BOARD_BASE + tile_row * ART_BOARD_TILE_WIDTH, ART_BOARD_TILE_WIDTH, row_pixels);
    }
}

void art_draw_cell(uint8_t x, uint8_t y, uint8_t state, uint8_t board_index) BANKED {
    uint8_t pixel_x = (board_index % 5u) * ART_CELL_PIXELS;
    uint8_t pixel_y = (board_index / 5u) * ART_CELL_PIXELS;
    uint8_t phase = (pixel_x & 7u) >> 2;
    uint8_t tile_x = pixel_x >> 3;
    uint8_t tile_y = pixel_y >> 3;
    uint8_t row;
    uint8_t column;
    uint8_t mask;
    uint8_t first_mask = (uint8_t)~row_masks[phase][0];
    uint8_t last_mask = (uint8_t)~row_masks[phase][2];
    uint8_t scanline = pixel_y & 7u;
    uint8_t tiles[9];
    uint16_t offset;
    uint8_t *target = board_pixels + ((uint16_t)tile_y * ART_BOARD_TILE_WIDTH + tile_x) * 16u + scanline * 2u;
    const uint8_t *source = gameplay_cell_rows + (uint16_t)state * 240u + (uint16_t)phase * 120u;

    for (row = 0u; row < ART_CELL_PIXELS; ++row) {
        target[0] = (target[0] & first_mask) | source[0];
        target[1] = (target[1] & first_mask) | source[1];
        target[16] = source[2];
        target[17] = source[3];
        target[32] = (target[32] & last_mask) | source[4];
        target[33] = (target[33] & last_mask) | source[5];
        source += 6u;
        if (++scanline == 8u) {
            scanline = 0u;
            target += ART_BOARD_TILE_WIDTH * 16u - 14u;
        } else {
            target += 2u;
        }
    }
    if (board_index == 0u || board_index == 4u || board_index == 20u || board_index == 24u) {
        uint8_t corner_x = board_index % 5u ? 99u : 0u;
        uint8_t corner_y = board_index / 5u ? 99u : 0u;
        offset = ((uint16_t)(corner_y >> 3) * ART_BOARD_TILE_WIDTH + (corner_x >> 3)) * 16u;
        offset += (corner_y & 7u) * 2u;
        mask = (uint8_t)~(0x80u >> (corner_x & 7u));
        board_pixels[offset] &= mask;
        board_pixels[offset + 1u] &= mask;
    }
    for (row = 0u; row < 3u; ++row) {
        uint8_t first_tile = (tile_y + row) * ART_BOARD_TILE_WIDTH + tile_x;
        set_bkg_data(ART_BOARD_BASE + first_tile, 3u, board_pixels + (uint16_t)first_tile * 16u);
        for (column = 0u; column < 3u; ++column) {
            tiles[row * 3u + column] = ART_BOARD_BASE + first_tile + column;
        }
    }
    set_bkg_tiles(x + tile_x, y + tile_y, 3u, 3u, tiles);
}
