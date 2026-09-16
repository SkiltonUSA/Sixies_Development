#ifndef SIXIES_GENERATED_ART_H
#define SIXIES_GENERATED_ART_H

#include <gb/gb.h>
#include <stdint.h>

#define ART_FONT_COUNT 40u
#define ART_HUD_DIGIT_BASE 1u
#define ART_HUD_PLUS_TILE 11u
#define ART_HUD_SCORE_BASE 12u
#define ART_NEXT_DICE_BASE 15u
#define ART_NEXT_TILES 32u
#define ART_DICE_PIXELS 18u
#define ART_CELL_STATE_COUNT 21u
#define ART_OCCUPIED_CELL_STATE 20u
#define ART_CELL_PIXELS 20u
#define ART_BOARD_BASE 55u
#define ART_BOARD_TILES 169u
#define ART_BOARD_TILE_WIDTH 13u
#define ART_SCREEN_BOUNDARY_BASE 47u
#define ART_NEXT_PANEL_WIDTH 6u
#define ART_NEXT_PANEL_HEIGHT 7u
#define ART_INVALID_NEXT_TILES 26u
#define ART_SCORE_PANEL_BASE 224u
#define ART_SCORE_PANEL_TILES 24u
#define ART_SCORE_PANEL_TOP 31u
#define ART_CALLOUT_TILES 32u
#define ART_CALLOUT_BASE 0u
#define ART_CALLOUT_SPRITES 16u
#define ART_CALLOUT_SPRITE_WIDTH 8u
#define ART_CALLOUT_SPRITE_HEIGHT 2u
#define ART_BACKGROUND_PATTERN_TILE 255u
#define ART_CHAIN_REACTION_BASE 0u
#define ART_CHAIN_REACTION_TILES 32u
#define ART_CHAIN_REACTION_SPRITES 16u
#define ART_CHAIN_REACTION_SPRITE_WIDTH 8u
#define ART_CHAIN_REACTION_SPRITE_HEIGHT 2u
#define ART_CHAIN_REACTION_MAX_SPRITES 16u
#define ART_STAR_TILE 36u
#define ART_MERGE_PARTICLE_TILES 2u
#define ART_SCORE_POPUP_BASE 32u
#define ART_CHAIN_STAR_LOAD_BASE 38u
#define ART_CHAIN_STAR_BASE 38u
#define ART_CHAIN_STAR_TILES 4u
#define ART_GAME_MASCOT_BASE 42u
#define ART_GAME_MASCOT_WIDTH 5u
#define ART_GAME_MASCOT_HEIGHT 6u
#define ART_GAME_MASCOT_TILES 30u
#define ART_GAMEPLAY_TILE_COUNT 55u

#define ART_TITLE_LOGO_BASE 40u
#define ART_TITLE_MASCOT_BASE 130u
#define ART_TITLE_TILE_COUNT 178u
#define ART_TITLE_PROMPT_WIDTH 88u
#define ART_TITLE_PROMPT_TILES 10u
#define ART_INTRO_VERSION_BASE 0u
#define ART_INTRO_VERSION_TILES 12u
#define ART_INTRO_VERSION_V_TILE ART_INTRO_VERSION_BASE
#define ART_INTRO_VERSION_DOT_TILE (ART_INTRO_VERSION_BASE + 1u)
#define ART_INTRO_VERSION_DIGIT_BASE (ART_INTRO_VERSION_BASE + 2u)

extern const uint8_t gameplay_tiles[];
extern const uint8_t gameplay_cell_rows[];
extern const uint8_t gameplay_next_frame[];
extern const uint8_t gameplay_next_dice_rows[];
extern const uint8_t gameplay_next_maps[];
extern const uint8_t title_tiles[];

#define ART_BORDER_BASE 178u
#define ART_SCORE_MASCOT_BASE 184u
void art_load_game(void) BANKED;
void art_reset_board(void) BANKED;
void art_shift_board(uint8_t shifted) BANKED;
void art_draw_invalid_next(uint8_t x, uint8_t y) BANKED;
void art_load_menu_font(void) BANKED;
void art_load_merge_particle(void) BANKED;
void art_restore_game_sprite_font(void) BANKED;
void art_draw_cell(uint8_t x, uint8_t y, uint8_t state, uint8_t board_index) BANKED;
void art_draw_next_dice(uint8_t x, uint8_t y, uint8_t first, uint8_t second, uint8_t orientation) BANKED;
void art_load_title(void) BANKED;
void art_load_credits(void) BANKED;
void art_draw_callout(uint8_t index, uint8_t x, uint8_t y) BANKED;
void art_clear_callout(void) BANKED;
void art_draw_score(uint16_t value) BANKED;
void art_load_chain_reaction(void) BANKED;
void art_load_screen(uint8_t index) BANKED;
void art_load_credits_screen(void) BANKED;

uint8_t art_build_score_popup(uint16_t value) BANKED;

#define ART_INSTRUCTION_PAGES 1u
void art_load_instructions(void) BANKED;
void art_draw_instructions(uint8_t page) BANKED;

#define ART_RESULTS_TILE_COUNT 184u
#define ART_RESULTS_NUMBER_BASE 240u
extern const uint8_t results_tiles[];
extern const uint8_t results_map[];
extern const uint8_t results_attributes[];
extern const uint8_t results_palette[];
extern const uint8_t results_arrow_tiles[];
extern const uint8_t results_digit_rows[];
void art_load_results(uint16_t score, uint16_t best) BANKED;

#define ART_HIGHSCORE_TILE_COUNT 164u
#define ART_HIGHSCORE_PANEL_BASE 164u
#define ART_HIGHSCORE_FOOTER_BASE 236u
extern const uint8_t highscore_tiles[];
extern const uint8_t highscore_map[];
extern const uint8_t highscore_palette[];
extern const uint8_t highscore_panel[];
extern const uint8_t highscore_glyph_widths[];
extern const uint8_t highscore_glyph_rows[];
void art_load_highscores(void) BANKED;
void art_update_highscores(uint8_t page, uint8_t rank, uint8_t letter) BANKED;

void art_load_start_menu(void) BANKED;
void art_select_start_menu(uint8_t selection, uint8_t previous) BANKED;

void art_load_settings(void) BANKED;
void art_update_settings(uint8_t state) BANKED;

void art_load_pause(void) BANKED;
void art_update_pause(uint8_t selection, uint8_t sound, uint8_t full_flash) BANKED;

#endif
