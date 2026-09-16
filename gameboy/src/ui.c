#include <gb/gb.h>
#include <gb/cgb.h>
#include <stdint.h>

#include "effects.h"
#include "game.h"
#include "generated_art.h"
#include "ui.h"
#include "audio.h"
#include "scores.h"

#define BOARD_LEFT 0u
#define BOARD_TOP 0u
#define BOARD_INSET_X 5u
#define BOARD_INSET_Y 22u
#define NEXT_LEFT 13u
#define NEXT_TOP 6u
#define SIDEBAR_LEFT 14u
#define CHAIN_REACTION_FRAMES 60u
#define INVALID_FEEDBACK_FRAMES 19u
#define CHAIN_STAR_COUNT 2u
#define CHAIN_STAR_SPRITES_PER_STAR 2u
#define CHAIN_REACTION_SPRITE_BASE 4u
#define SCORE_FLIGHT_STEP 6u
#define HOVER_PHASE_FRAMES 8u
#define MERGE_PARTICLE_COUNT 8u

static const palette_color_t game_palette[] = {
    RGB8(255, 246, 194),
    RGB8(236, 178, 58),
    RGB8(38, 74, 116),
    RGB8(8, 16, 32),
};

static const palette_color_t grid_palette[] = {
    RGB8(229, 240, 183),
    RGB8(139, 172, 15),
    RGB8(48, 98, 48),
    RGB8(13, 56, 0),
};

static const palette_color_t boundary_palette[] = {
    RGB8(229, 240, 183),
    RGB8(139, 172, 15),
    RGB8(48, 98, 48),
    RGB8(0, 0, 0),
};

static const palette_color_t background_palette[] = {
    RGB8(195, 209, 166),
    RGB8(190, 210, 148),
    RGB8(48, 98, 48),
    RGB8(13, 56, 0),
};

static const palette_color_t panel_palette[] = {
    RGB8(229, 240, 183),
    RGB8(139, 172, 15),
    RGB8(48, 98, 48),
    RGB8(13, 56, 0),
};

static const palette_color_t score_popup_palette[] = {
    RGB8(229, 240, 183),
    RGB8(229, 240, 183),
    RGB8(139, 172, 15),
    RGB8(13, 56, 0),
};

static const palette_color_t grid_flash_palette[] = {
    RGB8(13, 56, 0),
    RGB8(48, 98, 48),
    RGB8(139, 172, 15),
    RGB8(229, 240, 183),
};

static const palette_color_t callout_sprite_palette[] = {
    RGB8(0, 0, 0),
    RGB8(229, 240, 183),
    RGB8(120, 72, 172),
    RGB8(13, 56, 0),
};

static const palette_color_t merge_particle_palette[] = {
    RGB8(0, 0, 0),
    RGB8(229, 240, 183),
    RGB8(236, 178, 58),
    RGB8(13, 56, 0),
};

static uint8_t reduced_flash;
static const palette_color_t chain_star_palettes[] = {
    RGB8(0, 0, 0), RGB8(229, 240, 183), RGB8(95, 125, 23), RGB8(13, 56, 0),
    RGB8(0, 0, 0), RGB8(229, 240, 183), RGB8(57, 100, 26), RGB8(13, 56, 0),
};
static const int8_t chain_star_velocity_x[] = {-3, 0, 3, -2, 3, -1, -3, 2, 1};
static const int8_t chain_star_velocity_y[] = {-3, -4, -3, 1, -2, 3, -1, 3, -4};
static volatile uint8_t chain_stars_active;
static volatile uint8_t chain_star_age;
static uint8_t chain_star_origin;
static uint8_t chain_reaction_y;
static uint8_t score_valid;
static uint16_t score_cache;
static uint8_t chain_reaction_timer;
static uint8_t cell_cache[25];
static uint8_t next_invalid;
static volatile uint8_t hover_enabled;
static volatile uint8_t hover_frames;
static uint8_t hover_variant;
static volatile uint8_t invalid_feedback_frames;
static void draw_next_preview(uint8_t force);
static void stop_chain_stars(void);
static volatile uint8_t credits_split_enabled;
static volatile uint8_t credits_scroll;

static uint8_t active_hover_variant(void) {
    return reduced_flash || hover_frames < HOVER_PHASE_FRAMES ? 1u : 0u;
}

#define CREDITS_TEXT_SPRITES 40u
#define CREDITS_GROUP_FRAMES 44u

static const char * const credits_groups[][3] = {
    {"DESIGN +", "CODE + ART", ""},
    {"D.Skilton", "", ""},
    {"TITLE MUSIC", "WE ARE", "THE REASON"},
    {"STUDIO313", "GAMES 2026", ""},
    {"STUDIO313", "(C)2026", ""},
};

static const uint8_t credits_group_line_counts[] = {
    2u, 1u, 3u, 2u, 2u,
};

static const palette_color_t credits_fade_palettes[][4] = {
    {RGB8(202, 220, 159), RGB8(202, 220, 159), RGB8(202, 220, 159), RGB8(202, 220, 159)},
    {RGB8(202, 220, 159), RGB8(139, 172, 15), RGB8(139, 172, 15), RGB8(139, 172, 15)},
    {RGB8(202, 220, 159), RGB8(48, 98, 48), RGB8(48, 98, 48), RGB8(13, 56, 0)},
};

static void credits_split(void) {
    if (credits_split_enabled) SCY_REG = credits_scroll;
}

static void credits_vblank(void) {
    uint8_t sprite;

    if (credits_split_enabled) SCY_REG = 0u;
    if (invalid_feedback_frames && !--invalid_feedback_frames) NR42_REG = 0u;
    if (hover_enabled) hover_frames = (hover_frames + 1u) & (HOVER_PHASE_FRAMES * 2u - 1u);
    if (chain_stars_active && ++chain_star_age >= CHAIN_REACTION_FRAMES) stop_chain_stars();
    if (chain_reaction_timer && !--chain_reaction_timer) {
        stop_chain_stars();
        LCDC_REG &= (uint8_t)~LCDCF_OBJ16;
        for (sprite = 0u; sprite < ART_CHAIN_REACTION_MAX_SPRITES; ++sprite) {
            move_sprite((uint8_t)(CHAIN_REACTION_SPRITE_BASE + sprite), 0u, 0u);
            set_sprite_prop((uint8_t)(CHAIN_REACTION_SPRITE_BASE + sprite), 0u);
        }
    }
}

static uint8_t glyph_tile(char glyph) {
    if (glyph >= 'a' && glyph <= 'z') glyph = (char)(glyph - ('a' - 'A'));
    if (glyph >= 'A' && glyph <= 'Z') return (uint8_t)(1u + glyph - 'A');
    if (glyph >= '0' && glyph <= '9') return (uint8_t)(27u + glyph - '0');
    if (glyph == '+') return 37u;
    if (glyph == '!') return 38u;
    if (glyph == ':') return 39u;
    if (glyph == '.') return 40u;
    if (glyph == '(') return 41u;
    if (glyph == ')') return 42u;
    return 0u;
}

static uint8_t credits_glyph_width(char glyph) {
    return glyph == ' ' ? 2u : 8u;
}

static void draw_credits_line(const char *text, int16_t top, uint8_t *sprite) {
    const char *character;
    int16_t left;
    uint8_t width = 0u;

    if (top < 32 || top > 104) return;
    for (character = text; *character; ++character) width += credits_glyph_width(*character);
    left = (int16_t)(160 - width) / 2;
    for (character = text; *character; ++character) {
        if (*character != ' ' && *sprite < CREDITS_TEXT_SPRITES) {
            set_sprite_tile(*sprite, glyph_tile(*character));
            set_sprite_prop(*sprite, 0u);
            move_sprite(*sprite, (uint8_t)(left + 8), (uint8_t)(top + 16));
            ++*sprite;
        }
        left += credits_glyph_width(*character);
    }
}

static void draw_credits_group(uint8_t group, uint8_t *sprite) {
    uint8_t line;
    uint8_t line_count = credits_group_line_counts[group];
    int16_t top = (int16_t)(144u - (uint16_t)(line_count * 8u + (line_count - 1u) * 6u)) / 2;

    for (line = 0u; line < line_count; ++line) {
        draw_credits_line(credits_groups[group][line], top, sprite);
        top += 14;
    }
}

static void set_credits_fade(uint8_t phase) {
    uint8_t level;

    if (phase < 6u || phase >= 38u) level = 0u;
    else if (phase < 12u || phase >= 32u) level = 1u;
    else level = 2u;
    if (_cpu == CGB_TYPE) set_sprite_palette(0u, 1u, credits_fade_palettes[level]);
    else if (level == 0u) OBP0_REG = DMG_PALETTE(DMG_WHITE, DMG_WHITE, DMG_WHITE, DMG_WHITE);
    else if (level == 1u) OBP0_REG = DMG_PALETTE(DMG_WHITE, DMG_WHITE, DMG_LITE_GRAY, DMG_DARK_GRAY);
    else OBP0_REG = DMG_PALETTE(DMG_WHITE, DMG_LITE_GRAY, DMG_DARK_GRAY, DMG_BLACK);
}

void draw_text(uint8_t x, uint8_t y, const char *text) {
    while (*text && x < 20u) {
        set_bkg_tile_xy(x++, y, glyph_tile(*text++));
    }
}

void draw_number(uint8_t x, uint8_t y, uint16_t value, uint8_t digits) {
    uint16_t divisor;
    uint8_t digit;

    divisor = 1u;
    while (--digits) divisor = (uint16_t)(divisor * 10u);
    do {
        digit = (uint8_t)(value / divisor);
        set_bkg_tile_xy(x++, y, (uint8_t)(ART_HUD_DIGIT_BASE + digit));
        value = (uint16_t)(value % divisor);
        divisor = (uint16_t)(divisor / 10u);
    } while (divisor);
}

void draw_linear(uint8_t x, uint8_t y, uint8_t base, uint8_t width, uint8_t height) {
    uint8_t tile_x;
    uint8_t tile_y;

    for (tile_y = 0u; tile_y < height; ++tile_y) {
        for (tile_x = 0u; tile_x < width; ++tile_x) {
            set_bkg_tile_xy((uint8_t)(x + tile_x), (uint8_t)(y + tile_y), base++);
        }
    }
}

static void draw_cell(uint8_t index, uint8_t face, uint8_t variant) {
    uint8_t x;
    uint8_t y;
    uint8_t state;

    if (cell_cache[index] == face + variant * 8u) return;
    cell_cache[index] = face + variant * 8u;
    x = BOARD_LEFT;
    y = BOARD_TOP;
    if (variant == 3u) {
        state = ART_OCCUPIED_CELL_STATE;
    } else if (!face) {
        state = variant ? 1u : 0u;
    } else {
        state = (uint8_t)(2u + face - 1u + variant * 6u);
    }
    art_draw_cell(x, y, state, index);
}

static void wait_frames(uint8_t frames) {
    while (frames--) {
        wait_vbl_done();
        service_animation_input();
    }
}

static void play_tone(uint8_t low, uint8_t high, uint8_t envelope) {
    if (!audio_enabled) return;
    NR21_REG = 0x80u;
    NR22_REG = envelope;
    NR23_REG = low;
    NR24_REG = (uint8_t)(0x80u | high);
}

static void move_score_popup(uint8_t x, uint8_t y, uint8_t width) {
    uint8_t sprite;

    for (sprite = 0u; sprite < 3u; ++sprite) {
        if (sprite * 8u < width) move_sprite(sprite, x + sprite * 8u + 8u, y + 16u);
        else move_sprite(sprite, 0u, 0u);
    }
}

static void present_score_award(uint8_t origin, uint16_t award) {
    uint8_t width = art_build_score_popup(award);
    uint8_t x = BOARD_INSET_X + origin % GAME_BOARD_WIDTH * ART_CELL_PIXELS + 10u - width / 2u;
    uint8_t y = BOARD_INSET_Y + origin / GAME_BOARD_WIDTH * ART_CELL_PIXELS - 9u;
    uint8_t target_x = 133u - width / 2u;
    uint8_t sprite;

    for (sprite = 0u; sprite < 3u; ++sprite) {
        set_sprite_tile(sprite, ART_SCORE_POPUP_BASE + sprite);
        set_sprite_prop(sprite, _cpu == CGB_TYPE ? 2u : S_PALETTE);
    }
    move_score_popup(x, y, width);
    SHOW_SPRITES;
    wait_frames(reduced_flash ? 16u : 1u);
    if (!reduced_flash) {
        while (x != target_x || y != 31u) {
            if (x < target_x) x = target_x - x > SCORE_FLIGHT_STEP ? x + SCORE_FLIGHT_STEP : target_x;
            else if (x > target_x) x = x - target_x > SCORE_FLIGHT_STEP ? x - SCORE_FLIGHT_STEP : target_x;
            if (y > 31u) y = y - 31u > SCORE_FLIGHT_STEP ? y - SCORE_FLIGHT_STEP : 31u;
            else if (y < 31u) y = 31u - y > SCORE_FLIGHT_STEP ? y + SCORE_FLIGHT_STEP : 31u;
            move_score_popup(x, y, width);
            wait_frames(1u);
        }
    }
    ui_draw_score();
    wait_frames(2u);
    for (sprite = 0u; sprite < 3u; ++sprite) {
        move_sprite(sprite, 0u, 0u);
        set_sprite_prop(sprite, 0u);
    }
}

static void draw_multiplier(uint8_t origin, uint8_t depth, uint8_t step) {
    uint8_t x;
    uint8_t y;

    x = (uint8_t)(BOARD_INSET_X + BOARD_LEFT * 8u + (origin % GAME_BOARD_WIDTH) * ART_CELL_PIXELS + 10u + step * 2u);
    y = (uint8_t)(BOARD_INSET_Y + BOARD_TOP * 8u + (origin / GAME_BOARD_WIDTH) * ART_CELL_PIXELS + 18u - step * 2u);
    set_sprite_tile(0u, 27u + depth % 10u);
    set_sprite_tile(1u, glyph_tile('X'));
    move_sprite(0u, x, y);
    move_sprite(1u, x + 8u, y);
    if (depth >= 10u) {
        set_sprite_tile(2u, 27u + depth / 10u);
        move_sprite(2u, x - 8u, y);
    }
    SHOW_SPRITES;
}

static void callout_position(uint8_t origin, uint8_t *x, uint8_t *y) {
    *x = origin % GAME_BOARD_WIDTH < 2u ? 41u : 5u;
    *y = origin / GAME_BOARD_WIDTH < 2u ? 88u : 26u;
}

static void stop_chain_stars(void) {
    uint8_t sprite;
    chain_stars_active = 0u;
    for (sprite = 0u; sprite < CHAIN_STAR_COUNT * CHAIN_STAR_SPRITES_PER_STAR; ++sprite) {
        move_sprite(sprite, 0u, 0u);
        set_sprite_prop(sprite, 0u);
    }
}

static void clear_chain_reaction(void) {
    uint8_t sprite;

    chain_reaction_timer = 0u;
    stop_chain_stars();
    for (sprite = 0u; sprite < ART_CHAIN_REACTION_MAX_SPRITES; ++sprite) {
        move_sprite((uint8_t)(CHAIN_REACTION_SPRITE_BASE + sprite), 0u, 0u);
        set_sprite_prop((uint8_t)(CHAIN_REACTION_SPRITE_BASE + sprite), 0u);
    }
    LCDC_REG &= (uint8_t)~LCDCF_OBJ16;
    art_restore_game_sprite_font();
}

static void tick_chain_stars(void) {
    uint8_t age;
    uint8_t burst;
    uint8_t step;
    uint8_t sprite;
    uint8_t sprite_slot;
    uint8_t variant;
    uint8_t velocity;
    int16_t origin_x;
    int16_t origin_y;
    int16_t position_x;
    int16_t position_y;

    if (!chain_stars_active) return;
    age = chain_star_age;
    if (age >= CHAIN_REACTION_FRAMES || reduced_flash) {
        stop_chain_stars();
        return;
    }
    burst = age / 20u;
    step = (age % 20u) / 2u;
    origin_x = BOARD_INSET_X + (chain_star_origin % GAME_BOARD_WIDTH) * ART_CELL_PIXELS + 2u;
    origin_y = BOARD_INSET_Y + (chain_star_origin / GAME_BOARD_WIDTH) * ART_CELL_PIXELS + 2u;
    for (sprite = 0u; sprite < CHAIN_STAR_COUNT; ++sprite) {
        sprite_slot = (uint8_t)(sprite * CHAIN_STAR_SPRITES_PER_STAR);
        velocity = burst * 3u + sprite;
        position_x = origin_x + (int16_t)chain_star_velocity_x[velocity] * step;
        position_y = origin_y + (int16_t)chain_star_velocity_y[velocity] * step + (step * step) / 4u;
        variant = (burst + sprite + (age >> 2u)) & 1u;
        set_sprite_tile(sprite_slot, ART_CHAIN_STAR_BASE);
        set_sprite_prop(sprite_slot, _cpu == CGB_TYPE ? 3u + variant : S_PALETTE);
        if (position_x < 1 || position_x > 143 || position_y < 1 || position_y > 127) {
            move_sprite(sprite_slot, 0u, 0u);
            move_sprite((uint8_t)(sprite_slot + 1u), 0u, 0u);
        } else {
            move_sprite(sprite_slot, (uint8_t)(position_x + 8), (uint8_t)(position_y + 16));
        }
    }
    SHOW_SPRITES;
}

static void present_chain_reaction(uint8_t origin) {
    uint8_t x;
    uint8_t y;
    uint8_t row;
    uint8_t column;
    uint8_t sprite;
    uint8_t width;
    uint8_t height;
    uint8_t tile_step;
    uint8_t sprite_height;

    draw_next_preview(1u);
    callout_position(origin, &x, &y);
    width = ART_CHAIN_REACTION_SPRITE_WIDTH;
    height = ART_CHAIN_REACTION_SPRITE_HEIGHT;
    tile_step = 2u;
    sprite_height = 16u;
    LCDC_REG |= LCDCF_OBJ16;
    chain_reaction_y = y;
    wait_vbl_done();
    art_load_chain_reaction();
    sprite = CHAIN_REACTION_SPRITE_BASE;
    for (row = 0u; row < height; ++row) {
        for (column = 0u; column < width; ++column) {
            set_sprite_tile(sprite, (uint8_t)(ART_CHAIN_REACTION_BASE + (row * width + column) * tile_step));
            set_sprite_prop(sprite, _cpu == CGB_TYPE ? 5u : 0u);
            move_sprite(sprite, (uint8_t)(x + column * 8u + 8u), (uint8_t)(y + row * sprite_height + 16u));
            ++sprite;
        }
    }
    chain_reaction_timer = CHAIN_REACTION_FRAMES;
    chain_star_origin = origin;
    chain_star_age = 0u;
    chain_stars_active = !reduced_flash;
    tick_chain_stars();
    SHOW_SPRITES;
}

static void draw_ripple_cell(int8_t x, int8_t y) {
    uint8_t index;

    if (x < 0 || x >= (int8_t)GAME_BOARD_WIDTH || y < 0 || y >= (int8_t)GAME_BOARD_WIDTH) return;
    index = (uint8_t)((uint8_t)y * GAME_BOARD_WIDTH + (uint8_t)x);
    draw_cell(index, game_state.board[index], 1u);
}

static void present_ripple(uint8_t origin, uint8_t diagonals) {
    int8_t origin_x;
    int8_t origin_y;
    int8_t step;
    int8_t left;
    int8_t right;
    int8_t top;
    int8_t bottom;

    origin_x = (int8_t)(origin % GAME_BOARD_WIDTH);
    origin_y = (int8_t)(origin / GAME_BOARD_WIDTH);
    for (step = 0; step < 5; ++step) {
        left = step < origin_x ? step : origin_x;
        right = 4 - step > origin_x ? 4 - step : origin_x;
        top = step < origin_y ? step : origin_y;
        bottom = 4 - step > origin_y ? 4 - step : origin_y;
        draw_ripple_cell(left, origin_y);
        draw_ripple_cell(right, origin_y);
        draw_ripple_cell(origin_x, top);
        draw_ripple_cell(origin_x, bottom);
        if (diagonals) {
            draw_ripple_cell(left, top);
            draw_ripple_cell(right, top);
            draw_ripple_cell(left, bottom);
            draw_ripple_cell(right, bottom);
        }
        wait_frames(2u);
        ui_draw_board();
    }
}

static void present_stars(uint8_t origin) {
    static const int8_t velocity_x[MERGE_PARTICLE_COUNT] = {-3, -2, 0, 2, 3, -3, 0, 3};
    static const int8_t velocity_y[MERGE_PARTICLE_COUNT] = {-3, -4, -5, -4, -3, 2, 4, 2};
    uint8_t center_x;
    uint8_t center_y;
    uint8_t frame;
    uint8_t sprite;

    center_x = (uint8_t)(BOARD_INSET_X + BOARD_LEFT * 8u + (origin % GAME_BOARD_WIDTH) * ART_CELL_PIXELS + 6u);
    center_y = (uint8_t)(BOARD_INSET_Y + BOARD_TOP * 8u + (origin / GAME_BOARD_WIDTH) * ART_CELL_PIXELS + 6u);
    LCDC_REG &= (uint8_t)~LCDCF_OBJ16;
    art_load_merge_particle();
    for (sprite = 0u; sprite < MERGE_PARTICLE_COUNT; ++sprite) {
        set_sprite_tile(sprite, ART_STAR_TILE);
        set_sprite_prop(sprite, _cpu == CGB_TYPE ? 6u : S_PALETTE);
    }
    SHOW_SPRITES;
    for (frame = 0u; frame < 12u; ++frame) {
        for (sprite = 0u; sprite < MERGE_PARTICLE_COUNT; ++sprite) {
            int16_t pixel_x = (int16_t)center_x + (int16_t)velocity_x[sprite] * frame;
            int16_t pixel_y = (int16_t)center_y + (int16_t)velocity_y[sprite] * frame + (frame * frame) / 3u;
            if (pixel_x < 0) pixel_x = 0;
            else if (pixel_x > 152) pixel_x = 152;
            if (pixel_y < 0) pixel_y = 0;
            else if (pixel_y > 136) pixel_y = 136;
            move_sprite(sprite, (uint8_t)(pixel_x + 8), (uint8_t)(pixel_y + 16));
        }
        wait_frames(2u);
    }
    for (sprite = 0u; sprite < MERGE_PARTICLE_COUNT; ++sprite) move_sprite(sprite, 0u, 0u);
    if (chain_reaction_timer) SHOW_SPRITES;
    else HIDE_SPRITES;
}

void ui_initialize(void) {
    DISPLAY_OFF;
    credits_split_enabled = 0u;
    credits_scroll = 0u;
    LYC_REG = 72u;
    STAT_REG |= STATF_LYC;
    add_VBL(credits_vblank);
    add_LCD(credits_split);
    set_interrupts(VBL_IFLAG | LCD_IFLAG);
    if (_cpu == CGB_TYPE) {
        set_bkg_palette(0u, 1u, game_palette);
        set_sprite_palette(0u, 1u, game_palette);
    } else {
        BGP_REG = DMG_PALETTE(DMG_WHITE, DMG_LITE_GRAY, DMG_DARK_GRAY, DMG_BLACK);
        OBP0_REG = DMG_PALETTE(DMG_WHITE, DMG_LITE_GRAY, DMG_DARK_GRAY, DMG_BLACK);
    }
    reduced_flash = score_table.reduced_flash;
    SHOW_BKG;
    DISPLAY_ON;
}

void ui_prepare_screen(void) {
    uint8_t index;
    score_valid = 0u;
    hover_enabled = 0u;
    audio_scene_load_begin();
    DISPLAY_OFF;
    LCDC_REG &= (uint8_t)~LCDCF_OBJ16;
    HIDE_SPRITES;
    chain_reaction_timer = 0u;
    stop_chain_stars();
    if (invalid_feedback_frames) NR42_REG = 0u;
    invalid_feedback_frames = 0u;
    for (index = 0u; index < ART_CHAIN_REACTION_SPRITES; ++index) {
        move_sprite((uint8_t)(CHAIN_REACTION_SPRITE_BASE + index), 0u, 0u);
    }
    credits_split_enabled = 0u;
    SCX_REG = SCY_REG = 0u;
    next_invalid = 255u;
    for (index = 0u; index < 25u; ++index) cell_cache[index] = 255u;
    if (_cpu == CGB_TYPE) {
        VBK_REG = 1u;
        fill_bkg_rect(0u, 0u, 32u, 32u, 0u);
        VBK_REG = 0u;
        set_bkg_palette(0u, 1u, game_palette);
    } else {
        BGP_REG = DMG_PALETTE(DMG_WHITE, DMG_LITE_GRAY, DMG_DARK_GRAY, DMG_BLACK);
    }
    fill_bkg_rect(0u, 0u, 32u, 32u, 0u);
}

void ui_finish_screen(void) {
    DISPLAY_ON;
    audio_scene_load_end();
}

void ui_scroll_credits(uint8_t offset) {
    uint8_t group;
    uint8_t phase;
    uint8_t sprite = 0u;

    credits_scroll = offset;
    credits_split_enabled = 0u;
    SCY_REG = 0u;
    group = offset / CREDITS_GROUP_FRAMES;
    if (group >= sizeof(credits_groups) / sizeof(credits_groups[0])) group = sizeof(credits_groups) / sizeof(credits_groups[0]) - 1u;
    phase = offset % CREDITS_GROUP_FRAMES;
    set_credits_fade(phase);
    draw_credits_group(group, &sprite);
    while (sprite < CREDITS_TEXT_SPRITES) move_sprite(sprite++, 0u, 0u);
    SHOW_SPRITES;
}

void ui_draw_score(void) {
    if (score_valid && score_cache == game_state.score) return;
    art_draw_score(game_state.score);
    score_cache = game_state.score;
    score_valid = 1u;
}

void ui_draw_board(void) {
    uint8_t index;

    for (index = 0u; index < GAME_BOARD_SIZE; ++index) draw_cell(index, game_state.board[index], 0u);
}

void ui_draw_piece_preview(void) {
    uint8_t origin;
    uint8_t second = 255u;

    if (!hover_enabled) {
        hover_frames = 0u;
        hover_variant = 1u;
        hover_enabled = 1u;
    }
    hover_variant = active_hover_variant();
    draw_next_preview(0u);
    origin = (uint8_t)(game_state.cursor_y * GAME_BOARD_WIDTH + game_state.cursor_x);
    if (game_state.piece_count == 2u) {
        if (game_state.orientation == 0u && game_state.cursor_x + 1u < GAME_BOARD_WIDTH) second = (uint8_t)(origin + 1u);
        else if (game_state.orientation == 1u && game_state.cursor_y + 1u < GAME_BOARD_WIDTH) second = (uint8_t)(origin + GAME_BOARD_WIDTH);
        else if (game_state.orientation == 2u && game_state.cursor_x) second = (uint8_t)(origin - 1u);
        else if (game_state.orientation == 3u && game_state.cursor_y) second = (uint8_t)(origin - GAME_BOARD_WIDTH);
    }
    if (game_state.board[origin] || (game_state.piece_count == 2u && second == 255u)) draw_cell(origin, 0u, 3u);
    else draw_cell(origin, game_state.piece_first, hover_variant);
    if (second != 255u) {
        if (game_state.board[second]) draw_cell(second, 0u, 3u);
        else draw_cell(second, game_state.piece_second, hover_variant);
    }
}

static void draw_next_preview(uint8_t force) {
    uint8_t invalid_overlay = invalid_feedback_frames != 0u;

    if (!force && invalid_overlay == next_invalid) return;
    fill_bkg_rect(NEXT_LEFT, NEXT_TOP, 6u, 1u, 0u);
    if (invalid_overlay) {
        art_draw_invalid_next(NEXT_LEFT, NEXT_TOP + 1u);
        next_invalid = invalid_overlay;
        return;
    }
    next_invalid = 0u;
    art_draw_next_dice(NEXT_LEFT, NEXT_TOP + 1u, game_state.piece_first,
        game_state.piece_count == 2u ? game_state.piece_second : 0u, game_state.orientation);
}

static void draw_game_state(uint8_t show_hover) {
    ui_draw_score();
    draw_next_preview(1u);
    ui_draw_board();
    if (show_hover) ui_draw_piece_preview();
}

static void draw_screen_boundary(void) {
    uint8_t row;

    fill_bkg_rect(0u, 29u, 19u, 1u, ART_SCREEN_BOUNDARY_BASE);
    fill_bkg_rect(0u, 15u, 19u, 1u, ART_SCREEN_BOUNDARY_BASE + 1u);
    for (row = 0u; row < 32u; ++row) {
        if (row >= 15u && row <= 29u) continue;
        set_bkg_tile_xy(31u, row, ART_SCREEN_BOUNDARY_BASE + 2u);
        set_bkg_tile_xy(19u, row, ART_SCREEN_BOUNDARY_BASE + 3u);
    }
    set_bkg_tile_xy(31u, 29u, ART_SCREEN_BOUNDARY_BASE + 4u);
    set_bkg_tile_xy(19u, 29u, ART_SCREEN_BOUNDARY_BASE + 5u);
    set_bkg_tile_xy(31u, 15u, ART_SCREEN_BOUNDARY_BASE + 6u);
    set_bkg_tile_xy(19u, 15u, ART_SCREEN_BOUNDARY_BASE + 7u);
    if (_cpu == CGB_TYPE) {
        VBK_REG = 1u;
        fill_bkg_rect(0u, 29u, 20u, 1u, 2u);
        fill_bkg_rect(0u, 15u, 20u, 1u, 2u);
        fill_bkg_rect(31u, 29u, 1u, 3u, 2u);
        fill_bkg_rect(31u, 0u, 1u, 16u, 2u);
        fill_bkg_rect(19u, 29u, 1u, 3u, 2u);
        fill_bkg_rect(19u, 0u, 1u, 16u, 2u);
        VBK_REG = 0u;
    }
}

static void show_game(uint8_t show_hover) {
    ui_prepare_screen();
    art_load_game();
    fill_bkg_rect(0u, 0u, 32u, 32u, ART_BACKGROUND_PATTERN_TILE);
    if (_cpu == CGB_TYPE) {
        set_bkg_palette(1u, 1u, grid_palette);
        set_bkg_palette(2u, 1u, boundary_palette);
        set_bkg_palette(3u, 1u, background_palette);
        set_bkg_palette(4u, 1u, panel_palette);
        set_sprite_palette(2u, 1u, score_popup_palette);
        set_sprite_palette(3u, 2u, chain_star_palettes);
        set_sprite_palette(5u, 1u, callout_sprite_palette);
        set_sprite_palette(6u, 1u, merge_particle_palette);
        VBK_REG = 1u;
        fill_bkg_rect(0u, 0u, 32u, 32u, 3u);
        fill_bkg_rect(BOARD_LEFT, BOARD_TOP, ART_BOARD_TILE_WIDTH, ART_BOARD_TILE_WIDTH, 1u);
        fill_bkg_rect(13u, ART_SCORE_PANEL_TOP, 6u, 1u, 4u);
        fill_bkg_rect(13u, 0u, 6u, 3u, 4u);
        fill_bkg_rect(NEXT_LEFT, NEXT_TOP + 1u, 6u, 6u, 4u);
        VBK_REG = 0u;
    } else {
        BGP_REG = DMG_PALETTE(DMG_WHITE, DMG_LITE_GRAY, DMG_DARK_GRAY, DMG_BLACK);
        OBP0_REG = DMG_PALETTE(DMG_BLACK, DMG_DARK_GRAY, DMG_LITE_GRAY, DMG_WHITE);
        OBP1_REG = DMG_PALETTE(DMG_WHITE, DMG_WHITE, DMG_LITE_GRAY, DMG_BLACK);
    }
    draw_game_state(show_hover);
    draw_screen_boundary();
    SHOW_SPRITES;
    SCX_REG = (uint8_t)(0u - BOARD_INSET_X);
    SCY_REG = (uint8_t)(0u - BOARD_INSET_Y);
    ui_finish_screen();
}

void ui_show_game_start(void) {
    show_game(0u);
}

void ui_show_game(void) {
    show_game(1u);
}

void ui_refresh_game(void) {
    draw_game_state(1u);
}

void ui_start_spiral(void) {
    static const uint8_t spiral[] = {
        20u, 15u, 10u, 5u, 0u, 1u, 2u, 3u, 4u, 9u,
        14u, 19u, 24u, 23u, 22u, 21u, 16u, 11u, 6u, 7u,
        8u, 13u, 18u, 17u, 12u,
    };
    uint8_t index;

    if (!reduced_flash) {
        for (index = 0u; index < GAME_BOARD_SIZE; index += 2u) {
            draw_cell(spiral[index], game_state.board[spiral[index]], 1u);
            play_tone((uint8_t)(0x20u + index * 6u), 6u, 0x51u);
            if (index + 1u < GAME_BOARD_SIZE) {
                draw_cell(spiral[index + 1u], game_state.board[spiral[index + 1u]], 1u);
                play_tone((uint8_t)(0x20u + (index + 1u) * 6u), 6u, 0x51u);
            }
            wait_frames(1u);
            draw_cell(spiral[index], game_state.board[spiral[index]], 0u);
            if (index + 1u < GAME_BOARD_SIZE) draw_cell(spiral[index + 1u], game_state.board[spiral[index + 1u]], 0u);
        }
    }
    ui_draw_piece_preview();
}

void ui_tick(void) {
    uint8_t variant = active_hover_variant();

    tick_chain_stars();
    draw_next_preview(0u);
    if (hover_enabled && variant != hover_variant) {
        hover_variant = variant;
        ui_draw_piece_preview();
    }
}

void ui_toggle_reduced_flash(void) {
    reduced_flash ^= 1u;
    if (reduced_flash) stop_chain_stars();
    hover_frames = 0u;
    hover_variant = 1u;
    score_table.reduced_flash = reduced_flash;
}

uint8_t ui_reduced_flash(void) {
    return reduced_flash;
}

void ui_play_move(void) {
    play_tone(0x20u, 0x07u, 0x51u);
}

void ui_play_rotate(void) {
    play_tone(0x80u, 0x06u, 0x61u);
}

void ui_play_place(void) {
    play_tone(0xD0u, 0x05u, 0x91u);
}

void ui_play_invalid(void) {
    if (!audio_enabled) return;
    NR41_REG = 0x10u;
    NR42_REG = 0xA2u;
    NR43_REG = 0x35u;
    NR44_REG = 0x80u;
    invalid_feedback_frames = INVALID_FEEDBACK_FRAMES;
    draw_next_preview(0u);
}

void effects_present_merge(
    uint8_t consumed_face,
    uint8_t group_count,
    uint8_t origin,
    uint8_t chain_depth,
    uint16_t award,
    uint8_t callout
) {
    uint8_t step;
    uint8_t callout_x;
    uint8_t callout_y;

    (void)group_count;
    clear_chain_reaction();
    hover_enabled = 0u;
    ui_draw_board();
    play_tone((uint8_t)(0x20u + consumed_face * 28u), 7u, 0xC2u);

    if (consumed_face >= 5u && !reduced_flash) {
        art_shift_board(1u);
        wait_frames(1u);
        art_shift_board(0u);
        wait_frames(1u);
        if (consumed_face == 6u) {
            art_shift_board(1u);
            wait_frames(1u);
            art_shift_board(0u);
            wait_frames(1u);
        }
    }
    if (consumed_face == 6u && !reduced_flash) {
        if (_cpu == CGB_TYPE) set_bkg_palette(1u, 1u, grid_flash_palette);
        else BGP_REG = DMG_PALETTE(DMG_BLACK, DMG_DARK_GRAY, DMG_LITE_GRAY, DMG_WHITE);
        wait_frames(5u);
        if (_cpu == CGB_TYPE) set_bkg_palette(1u, 1u, grid_palette);
        else BGP_REG = DMG_PALETTE(DMG_WHITE, DMG_LITE_GRAY, DMG_DARK_GRAY, DMG_BLACK);
    }
    if (!reduced_flash) {
        present_ripple(origin, consumed_face >= 5u);
    }
    present_stars(origin);

    present_score_award(origin, award);
    ui_draw_board();

    if (chain_depth >= 2u) {
        for (step = 0u; step < 5u; ++step) {
            ui_draw_board();
            draw_multiplier(origin, chain_depth, step);
            wait_frames(2u);
        }
        ui_draw_board();
        HIDE_SPRITES;
        for (step = 0u; step < 3u; ++step) move_sprite(step, 0u, 0u);
    }

    if (chain_depth >= 2u) {
        present_chain_reaction(origin);
    } else {
        callout_position(origin, &callout_x, &callout_y);
        art_draw_callout(callout, callout_x, callout_y);
        wait_frames(30u);
        art_clear_callout();
        draw_game_state(1u);
    }
}
