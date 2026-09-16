#pragma bank 4
#include <gb/gb.h>
#include <gb/cgb.h>
#include "ui.h"
#include "game.h"
#include "scores.h"
#include "audio.h"
#include "build_version.h"
#include "generated_art.h"

static uint8_t start_menu_selection;
static uint8_t highscore_page;
static uint8_t highscore_clock;
static uint8_t highscore_delay;
static int8_t highscore_offset;
static int8_t highscore_direction;

static const palette_color_t title_text_palette[] = {
    RGB8(230, 255, 206),
    RGB8(132, 197, 107),
    RGB8(49, 107, 82),
    RGB8(0, 25, 33),
};

static const palette_color_t intro_version_palette[] = {
    RGB8(0, 0, 0),
    RGB8(0, 0, 0),
    RGB8(0, 0, 0),
    RGB8(13, 56, 0),
};

#define INTRO_VERSION_SPRITES 12u

static void set_title_prompt_sprites(uint8_t visible) {
    uint8_t sprite;

    for (sprite = 0u; sprite < ART_TITLE_PROMPT_TILES; ++sprite) {
        if (visible) {
            set_sprite_tile(sprite, sprite);
            set_sprite_prop(sprite, 0u);
            move_sprite(sprite, (uint8_t)((160u - ART_TITLE_PROMPT_WIDTH) / 2u + sprite * 8u + (sprite >= 5u ? 8u : 0u) + 8u), 132u);
        } else {
            move_sprite(sprite, 0u, 0u);
        }
    }
}

static void set_intro_version_sprites(void) {
    uint32_t major = SIXIES_BUILD_VERSION / 100u;
    uint8_t digits[8];
    uint8_t digit_count = 0u;
    uint8_t character_count;
    uint8_t character;
    uint8_t minor_tens = (uint8_t)((SIXIES_BUILD_VERSION % 100u) / 10u);
    uint8_t minor_ones = (uint8_t)(SIXIES_BUILD_VERSION % 10u);
    uint8_t vertical_offset;

    do {
        digits[digit_count++] = (uint8_t)(major % 10u);
        major /= 10u;
    } while (major);

    character_count = (uint8_t)(digit_count + 4u);
    vertical_offset = character_count > 10u ? 136u : 144u;
    for (character = 0u; character < INTRO_VERSION_SPRITES; ++character) {
        uint8_t tile;

        if (character >= character_count) {
            move_sprite((uint8_t)(ART_INTRO_VERSION_BASE + character), 0u, 0u);
            continue;
        }
        if (character == 0u) tile = ART_INTRO_VERSION_V_TILE;
        else if (character <= digit_count) tile = (uint8_t)(ART_INTRO_VERSION_DIGIT_BASE + digits[digit_count - character]);
        else if (character == digit_count + 1u) tile = ART_INTRO_VERSION_DOT_TILE;
        else if (character == digit_count + 2u) tile = (uint8_t)(ART_INTRO_VERSION_DIGIT_BASE + minor_tens);
        else tile = (uint8_t)(ART_INTRO_VERSION_DIGIT_BASE + minor_ones);
        set_sprite_tile((uint8_t)(ART_INTRO_VERSION_BASE + character), tile);
        set_sprite_prop((uint8_t)(ART_INTRO_VERSION_BASE + character), 0u);
        move_sprite((uint8_t)(ART_INTRO_VERSION_BASE + character), (uint8_t)(12u + (character % 10u) * 8u), (uint8_t)(vertical_offset + (character / 10u) * 8u));
    }
}

static void text_page(const char *heading) {
    uint8_t column;
    ui_prepare_screen();
    art_load_title();
    art_load_menu_font();
    draw_text(1u, 0u, "SIXIES GAME BOY");
    draw_text(1u, 2u, heading);
    for (column = 0u; column < 20u; ++column) {
        set_bkg_tile_xy(column, 1u, ART_BORDER_BASE);
        set_bkg_tile_xy(column, 3u, ART_BORDER_BASE);
    }
    set_bkg_tile_xy(0u, 2u, ART_BORDER_BASE + 1u);
    set_bkg_tile_xy(19u, 2u, ART_BORDER_BASE + 1u);
}

void ui_show_intro(void) BANKED {
    ui_prepare_screen();
    art_load_screen(2u);
    if (_cpu == CGB_TYPE) set_sprite_palette(0u, 1u, intro_version_palette);
    else OBP0_REG = DMG_PALETTE(DMG_BLACK, DMG_BLACK, DMG_BLACK, DMG_DARK_GRAY);
    set_intro_version_sprites();
    SHOW_SPRITES;
    ui_finish_screen();
}

void ui_show_title(uint16_t best_score) BANKED {
    (void)best_score;
    ui_prepare_screen();
    art_load_screen(0u);
    if (_cpu == CGB_TYPE) set_sprite_palette(0u, 1u, title_text_palette);
    else OBP0_REG = DMG_PALETTE(DMG_WHITE, DMG_LITE_GRAY, DMG_DARK_GRAY, DMG_BLACK);
    set_title_prompt_sprites(1u);
    SHOW_SPRITES;
    ui_finish_screen();
}

void ui_set_title_prompt(uint8_t visible) BANKED {
    set_title_prompt_sprites(visible);
    SHOW_SPRITES;
}

void ui_show_start_menu(uint8_t selection) BANKED {
    uint8_t sprite;

    ui_prepare_screen();
    art_load_start_menu();
    OBP0_REG = DMG_PALETTE(DMG_WHITE, DMG_LITE_GRAY, DMG_DARK_GRAY, DMG_BLACK);
    for (sprite = 0u; sprite < 40u; ++sprite) move_sprite(sprite, 0u, 0u);
    for (sprite = 0u; sprite < 2u; ++sprite) {
        set_sprite_tile(sprite, sprite);
        set_sprite_prop(sprite, 0u);
    }
    start_menu_selection = 255u;
    ui_update_start_menu(selection);
    SHOW_SPRITES;
    ui_finish_screen();
}

void ui_update_start_menu(uint8_t selection) BANKED {
    static const uint8_t option_tops[4] = {64u, 79u, 92u, 105u};

    art_select_start_menu(selection, start_menu_selection);
    start_menu_selection = selection;
    move_sprite(0u, 90u, option_tops[selection] + 16u);
    move_sprite(1u, 90u, option_tops[selection] + 24u);
}

void ui_show_settings(uint8_t selection) BANKED {
    ui_prepare_screen();
    art_load_settings();
    ui_update_settings(selection);
    ui_finish_screen();
}

void ui_update_settings(uint8_t selection) BANKED {
    art_update_settings((uint8_t)(selection * 4u + (audio_enabled ? 2u : 0u) + (ui_reduced_flash() ? 0u : 1u)));
}

void ui_show_menu_scores(void) BANKED {
    ui_show_scores(SCORE_COUNT, 0u);
}

void ui_turn_score_page(void) BANKED {
    highscore_page ^= 1u;
    HIDE_SPRITES;
    art_update_highscores(highscore_page, SCORE_COUNT, 0u);
    highscore_clock = (uint8_t)sys_time;
    highscore_delay = 60u;
    highscore_offset = 0;
    highscore_direction = 1;
}

void ui_tick_scores(void) BANKED {
    uint8_t now = (uint8_t)sys_time;
    uint8_t elapsed = now - highscore_clock;
    uint8_t sprite;
    uint8_t moved = 0u;
    highscore_clock = now;
    if (highscore_page) return;
    while (elapsed--) {
        if (--highscore_delay) continue;
        highscore_delay = 6u;
        highscore_offset += highscore_direction;
        if (highscore_offset == 3 || highscore_offset == -3) highscore_direction = -highscore_direction;
        moved = 1u;
    }
    if (moved) {
        for (sprite = 0u; sprite < 9u; ++sprite) move_sprite(sprite, 88u + sprite * 8u + highscore_offset, 76u);
    }
}

void ui_show_credits(void) BANKED {
    ui_prepare_screen();
    art_load_credits_screen();
    if (_cpu == CGB_TYPE) set_sprite_palette(0u, 1u, title_text_palette);
    else OBP0_REG = DMG_PALETTE(DMG_WHITE, DMG_LITE_GRAY, DMG_DARK_GRAY, DMG_BLACK);
    if (_cpu != CGB_TYPE) BGP_REG = DMG_PALETTE(DMG_BLACK, DMG_DARK_GRAY, DMG_LITE_GRAY, DMG_WHITE);
    ui_scroll_credits(0u);
    ui_finish_screen();
}

void ui_show_instructions(uint8_t page) BANKED {
    ui_prepare_screen();
    art_load_instructions();
    ui_update_instructions(page);
    ui_finish_screen();
}

void ui_update_instructions(uint8_t page) BANKED {
    art_draw_instructions(page);
}

void ui_show_game_over(uint16_t best_score) BANKED {
    (void)best_score;
    ui_prepare_screen();
    art_load_screen(1u);
    ui_finish_screen();
}

void ui_show_results(uint16_t score, uint16_t best) BANKED {
    uint8_t sprite;

    ui_prepare_screen();
    art_load_results(score, best);
    OBP0_REG = DMG_PALETTE(DMG_WHITE, DMG_LITE_GRAY, DMG_DARK_GRAY, DMG_BLACK);
    for (sprite = 0u; sprite < 40u; ++sprite) move_sprite(sprite, 0u, 0u);
    for (sprite = 0u; sprite < 2u; ++sprite) {
        set_sprite_tile(sprite, sprite);
        set_sprite_prop(sprite, 0u);
    }
    ui_update_results(0u);
    SHOW_SPRITES;
    ui_finish_screen();
}

void ui_update_results(uint8_t selection) BANKED {
    move_sprite(0u, 78u, (uint8_t)(100u + selection * 14u));
    move_sprite(1u, 78u, (uint8_t)(108u + selection * 14u));
}

void ui_show_scores(uint8_t rank, uint8_t letter) BANKED {
    ui_prepare_screen();
    highscore_page = rank < SCORE_COUNT ? rank / 5u : 0u;
    art_load_highscores();
    art_update_highscores(highscore_page, rank, letter);
    ui_finish_screen();
    highscore_clock = (uint8_t)sys_time;
    highscore_delay = 60u;
    highscore_offset = 0;
    highscore_direction = 1;
}

void ui_update_initials(uint8_t rank, uint8_t letter) BANKED {
    art_update_highscores(highscore_page, rank, letter);
}

void ui_show_pause(uint8_t selection) BANKED {
    ui_prepare_screen();
    art_load_pause();
    ui_update_pause(selection);
    ui_finish_screen();
}

void ui_update_pause(uint8_t selection) BANKED {
    art_update_pause(selection, audio_enabled, (uint8_t)!ui_reduced_flash());
}

void ui_show_confirm(void) BANKED {
    text_page("START A NEW GAME");
    draw_text(1u, 6u, "CURRENT GAME ENDS");
    draw_text(1u, 9u, "A NEW GAME");
    draw_text(1u, 11u, "B CANCEL");
    ui_finish_screen();
}
