#pragma bank 7
#include <gb/gb.h>
#include <stdint.h>
#include <string.h>

#include "generated_art.h"

static uint8_t cached_tiles[ART_NEXT_TILES * 16u];
static uint8_t cached_map[36];
static uint8_t cached_count;
static uint8_t cached_first;
static uint8_t cached_second;
static uint8_t cached_orientation;

static void paste_die(uint8_t *pixels, uint8_t face, uint8_t left, uint8_t top) {
    uint8_t phase = left == 6u ? 1u : left == 15u ? 2u : 0u;
    const uint8_t *source = gameplay_next_dice_rows + (uint16_t)(face - 1u) * 432u + (uint16_t)phase * 144u;
    uint8_t *target = pixels + ((uint16_t)(top >> 3) * 6u + (left >> 3)) * 16u + (top & 7u) * 2u;
    uint8_t first_mask = phase == 1u ? 0xFCu : phase == 2u ? 0xFEu : 0u;
    uint8_t last_mask = phase ? 0u : 0x3Fu;
    uint8_t scanline = top & 7u;
    uint8_t row;

    for (row = 0u; row < ART_DICE_PIXELS; ++row) {
        target[0] = (target[0] & first_mask) | source[0];
        target[1] = (target[1] & first_mask) | source[1];
        target[16] = source[2];
        target[17] = source[3];
        target[32] = (target[32] & last_mask) | source[4];
        target[33] = (target[33] & last_mask) | source[5];
        if (phase == 2u) {
            target[48] = (target[48] & 0x7Fu) | source[6];
            target[49] = (target[49] & 0x7Fu) | source[7];
        }
        source += 8u;
        if (++scanline == 8u) {
            scanline = 0u;
            target += 82u;
        } else {
            target += 2u;
        }
    }
}

void art_draw_next_dice(uint8_t x, uint8_t y, uint8_t first, uint8_t second, uint8_t orientation) BANKED {
    static const uint8_t positions[4][4] = {
        {6u, 15u, 24u, 15u}, {15u, 6u, 15u, 24u},
        {24u, 15u, 6u, 15u}, {15u, 24u, 15u, 6u},
    };
    uint8_t pixels[36u * 16u];
    uint8_t count = 0u;
    uint8_t tile;
    uint8_t match;
    uint8_t state = second ? 6u + ((first - 1u) * 6u + second - 1u) * 4u + (orientation & 3u) : first - 1u;
    const uint8_t *position = positions[orientation & 3u];

    if (cached_count && first == cached_first && second == cached_second && orientation == cached_orientation) {
        set_bkg_data(ART_NEXT_DICE_BASE, cached_count, cached_tiles);
        set_bkg_tiles(x, y, 6u, 6u, cached_map);
        return;
    }
    memcpy(pixels, gameplay_next_frame, sizeof(pixels));
    if (second) {
        paste_die(pixels, first, position[0], position[1]);
        paste_die(pixels, second, position[2], position[3]);
    } else {
        paste_die(pixels, first, 15u, 15u);
    }
    memcpy(cached_map, gameplay_next_maps + (uint16_t)state * 36u, sizeof(cached_map));
    for (tile = 0u; tile < 36u; ++tile) {
        match = cached_map[tile];
        if (match == ART_NEXT_DICE_BASE + count) {
            memcpy(cached_tiles + (uint16_t)count * 16u, pixels + (uint16_t)tile * 16u, 16u);
            ++count;
        }
    }
    cached_count = count;
    cached_first = first;
    cached_second = second;
    cached_orientation = orientation;
    set_bkg_data(ART_NEXT_DICE_BASE, count, cached_tiles);
    set_bkg_tiles(x, y, 6u, 6u, cached_map);
}
