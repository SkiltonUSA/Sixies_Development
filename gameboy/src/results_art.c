#pragma bank 6
#include <gb/gb.h>
#include <gb/cgb.h>
#include <stdint.h>
#include <string.h>

#include "generated_art.h"

static void draw_result_number(uint8_t *pixels, uint16_t value, uint8_t top) {
    uint16_t divisor = 10000u;
    uint8_t digit;
    uint8_t column;
    uint8_t row;
    uint8_t position;

    for (position = 0u; position < 5u; ++position) {
        digit = (uint8_t)(value / divisor);
        value %= divisor;
        divisor /= 10u;
        for (row = 0u; row < 8u; ++row) {
            for (column = 0u; column < 6u; ++column) {
                uint8_t pixel_x = 3u + position * 7u + column;
                uint8_t pixel_y = top + row;
                uint16_t offset = ((uint16_t)(pixel_y / 8u) * 5u + pixel_x / 8u) * 16u + (pixel_y & 7u) * 2u;
                uint8_t mask = 0x80u >> (pixel_x & 7u);
                if (results_digit_rows[digit * 8u + row] & (0x20u >> column)) {
                    pixels[offset] |= mask;
                    pixels[offset + 1u] |= mask;
                }
            }
        }
    }
}

void art_load_results(uint16_t score, uint16_t best) BANKED {
    uint8_t pixels[240];
    uint8_t tiles[15];
    uint8_t index;

    LCDC_REG &= (uint8_t)~LCDCF_BG8000;
    set_bkg_data(0u, ART_RESULTS_TILE_COUNT, results_tiles);
    set_bkg_tiles(0u, 0u, 20u, 18u, results_map);
    memset(pixels, 0, sizeof(pixels));
    draw_result_number(pixels, score, 4u);
    draw_result_number(pixels, best, 16u);
    for (index = 0u; index < 15u; ++index) tiles[index] = ART_RESULTS_NUMBER_BASE + index;
    set_bkg_data(ART_RESULTS_NUMBER_BASE, 15u, pixels);
    set_bkg_tiles(13u, 6u, 5u, 3u, tiles);
    set_sprite_data(0u, 2u, results_arrow_tiles);
    if (_cpu == CGB_TYPE) {
        set_bkg_palette(0u, 1u, (const palette_color_t *)results_palette);
        set_sprite_palette(0u, 1u, (const palette_color_t *)results_palette);
        VBK_REG = 1u;
        set_bkg_tiles(0u, 0u, 20u, 18u, results_attributes);
        VBK_REG = 0u;
    }
}
