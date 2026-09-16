#pragma bank 5
#include <gb/gb.h>
#include <gb/cgb.h>
#include <string.h>
#include "generated_art.h"
#include "scores.h"

static uint8_t cached_page;
static uint8_t cached_rank;

static uint8_t glyph_index(char character) {
    if (character >= '0' && character <= '9') return character - '0';
    if (character >= 'A' && character <= 'Z') return character - 'A' + 10u;
    if (character == '/') return 37u;
    if (character == ':') return 38u;
    return 36u;
}

static uint8_t text_width(const char *text, uint8_t count) {
    uint8_t width = 0u;
    while (count--) width += highscore_glyph_widths[glyph_index(*text++)] + 1u;
    return width - 1u;
}

static void put_pixel(uint8_t *pixels, uint8_t column, uint8_t row, uint8_t shade) {
    uint16_t offset = (uint16_t)(column / 8u) * 16u + row * 2u;
    uint8_t mask = 0x80u >> (column & 7u);
    pixels[offset] = (pixels[offset] & (uint8_t)~mask) | ((shade & 1u) ? mask : 0u);
    pixels[offset + 1u] = (pixels[offset + 1u] & (uint8_t)~mask) | ((shade & 2u) ? mask : 0u);
}

static uint8_t draw_character(uint8_t *pixels, char character, uint8_t left, uint8_t top, uint8_t strip, uint8_t selected) {
    uint8_t glyph = glyph_index(character);
    uint8_t width = highscore_glyph_widths[glyph];
    uint8_t row;
    uint8_t column;
    for (row = 0u; row < 8u; ++row) {
        uint8_t bits;
        if ((top + row) / 8u != strip) continue;
        bits = highscore_glyph_rows[(uint16_t)glyph * 8u + row];
        for (column = 0u; column < width; ++column) {
            if (bits & (0x80u >> column)) put_pixel(pixels, left + column, (top + row) & 7u, selected ? 1u : 3u);
            else if (selected) put_pixel(pixels, left + column, (top + row) & 7u, 3u);
        }
    }
    return width + 1u;
}

static void draw_entry_text(uint8_t *pixels, uint8_t strip, uint8_t index, uint8_t top, uint8_t rank, uint8_t floating) {
    uint8_t position;
    uint8_t left = 14u;
    uint8_t number_left = 38u;
    uint16_t value = score_table.entries[index].score;
    uint16_t divisor = 10000u;
    if (floating) {
        uint8_t initials_width = text_width(score_table.entries[0].initials, 3u);
        left = (72u - (initials_width + 35u)) / 2u;
        draw_character(pixels, '1', left, top, strip, 0u);
        left += 4u;
        number_left = left + initials_width + 1u;
    } else {
        if (index == 9u) draw_character(pixels, '1', 4u, top, strip, 0u);
        draw_character(pixels, '0' + (index + 1u) % 10u, 8u, top, strip, 0u);
    }
    if (index != rank) {
        for (position = 0u; position < 3u; ++position) left += draw_character(pixels, score_table.entries[index].initials[position], left, top, strip, 0u);
    }
    for (position = 0u; position < 5u; ++position) {
        draw_character(pixels, '0' + value / divisor, number_left + position * 6u, top, strip, 0u);
        value %= divisor;
        divisor /= 10u;
    }
}

static void draw_entry(uint8_t *pixels, uint8_t strip, uint8_t index, uint8_t top, uint8_t rank) {
    uint8_t row;
    uint8_t column;
    if (strip < (top - 1u) / 8u || strip > (top + 8u) / 8u) return;
    if (index == rank || (rank == SCORE_COUNT && index % 5u == 0u)) {
        for (row = top - 1u; row < top + 9u; ++row) {
            if (row / 8u != strip) continue;
            for (column = 0u; column < 9u; ++column) {
                uint8_t offset = column * 16u + (row & 7u) * 2u;
                uint8_t keep = column == 0u ? 0xF0u : column == 8u ? 0x0Fu : 0u;
                pixels[offset] &= keep;
                pixels[offset + 1u] &= keep;
            }
        }
    }
    if (index != 0u || rank != SCORE_COUNT) draw_entry_text(pixels, strip, index, top, rank, 0u);
}

static void draw_initials(uint8_t rank, uint8_t letter) {
    uint8_t pixels[64];
    uint8_t position;
    uint8_t left = 0u;
    memset(pixels, 0, sizeof(pixels));
    for (position = 0u; position < 3u; ++position) left += draw_character(pixels, score_table.entries[rank].initials[position], left, 0u, 0u, position == letter);
    set_sprite_data(0u, 4u, pixels);
    for (position = 0u; position < 4u; ++position) {
        set_sprite_tile(position, position);
        set_sprite_prop(position, 0u);
        move_sprite(position, 102u + position * 8u, 76u + (rank % 5u) * 11u);
    }
    SHOW_SPRITES;
}

void art_load_highscores(void) BANKED {
    uint8_t sprite;
    cached_page = cached_rank = 255u;
    for (sprite = 0u; sprite < 40u; ++sprite) move_sprite(sprite, 0u, 0u);
    LCDC_REG &= (uint8_t)~LCDCF_BG8000;
    set_bkg_data(0u, ART_HIGHSCORE_TILE_COUNT, highscore_tiles);
    set_bkg_tiles(0u, 0u, 20u, 18u, highscore_map);
    if (_cpu == CGB_TYPE) {
        set_bkg_palette(0u, 1u, (const palette_color_t *)highscore_palette);
        set_sprite_palette(0u, 1u, (const palette_color_t *)highscore_palette);
        set_sprite_palette_entry(0u, 1u, RGB8(214, 240, 168));
    }
    OBP0_REG = DMG_PALETTE(DMG_WHITE, DMG_WHITE, DMG_DARK_GRAY, DMG_BLACK);
}

void art_update_highscores(uint8_t page, uint8_t rank, uint8_t letter) BANKED {
    uint8_t pixels[144];
    uint8_t tilemap[20];
    uint8_t strip;
    uint8_t row;
    uint8_t column;
    uint8_t tile;
    uint8_t footer_pixels[320];
    const char *footer = "UP/DN SET A NEXT START SAVE";
    uint8_t length = (uint8_t)strlen(footer);
    uint8_t left = (160u - text_width(footer, length)) / 2u;
    uint8_t refresh_all = cached_page != page || cached_rank != rank;

    if (!refresh_all) {
        if (rank < SCORE_COUNT) draw_initials(rank, letter);
        return;
    }

    for (strip = 0u; strip < 8u; ++strip) {
        memcpy(pixels, highscore_panel + (uint16_t)strip * 144u, sizeof(pixels));
        for (row = 0u; row < 5u; ++row) draw_entry(pixels, strip, page * 5u + row, 4u + row * 11u, rank);
        for (column = 0u; column < 9u; ++column) tilemap[column] = ART_HIGHSCORE_PANEL_BASE + strip * 9u + column;
        set_bkg_data(tilemap[0], 9u, pixels);
        set_bkg_tiles(10u, 7u + strip, 9u, 1u, tilemap);
    }
    cached_page = page;
    cached_rank = rank;
    HIDE_SPRITES;
    if (rank == SCORE_COUNT) {
        if (page == 0u) {
            memset(pixels, 0, sizeof(pixels));
            draw_entry_text(pixels, 0u, 0u, 0u, SCORE_COUNT, 1u);
            set_sprite_data(0u, 9u, pixels);
            for (tile = 0u; tile < 9u; ++tile) {
                set_sprite_tile(tile, tile);
                set_sprite_prop(tile, 0u);
                move_sprite(tile, 88u + tile * 8u, 76u);
            }
            SHOW_SPRITES;
        }
        return;
    }
    memset(footer_pixels, 0, sizeof(footer_pixels));
    for (column = 0u; column < length; ++column) left += draw_character(footer_pixels, footer[column], left, 0u, 0u, 0u);
    for (tile = 0u; tile < 20u; ++tile) tilemap[tile] = ART_HIGHSCORE_FOOTER_BASE + tile;
    set_bkg_data(ART_HIGHSCORE_FOOTER_BASE, 20u, footer_pixels);
    set_bkg_tiles(0u, 16u, 20u, 1u, tilemap);
    draw_initials(rank, letter);
}
