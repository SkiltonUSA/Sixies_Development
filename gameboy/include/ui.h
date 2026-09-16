#ifndef SIXIES_UI_H
#define SIXIES_UI_H

#include <stdint.h>
#include <gb/gb.h>

void ui_initialize(void);
void ui_show_intro(void) BANKED;
void ui_show_title(uint16_t best_score) BANKED;
void ui_set_title_prompt(uint8_t visible) BANKED;
void ui_show_start_menu(uint8_t selection) BANKED;
void ui_update_start_menu(uint8_t selection) BANKED;
void ui_show_settings(uint8_t selection) BANKED;
void ui_update_settings(uint8_t selection) BANKED;
void ui_show_menu_scores(void) BANKED;
void ui_turn_score_page(void) BANKED;
void ui_tick_scores(void) BANKED;
void ui_show_instructions(uint8_t page) BANKED;
void ui_update_instructions(uint8_t page) BANKED;
void ui_show_credits(void) BANKED;
void ui_scroll_credits(uint8_t offset);
void ui_show_scores(uint8_t rank, uint8_t letter) BANKED;
void ui_update_initials(uint8_t rank, uint8_t letter) BANKED;
void ui_show_pause(uint8_t selection) BANKED;
void ui_update_pause(uint8_t selection) BANKED;
void ui_show_confirm(void) BANKED;
void ui_prepare_screen(void);
void ui_finish_screen(void);
void draw_text(uint8_t x, uint8_t y, const char *text);
void draw_number(uint8_t x, uint8_t y, uint16_t value, uint8_t digits);
void draw_linear(uint8_t x, uint8_t y, uint8_t base, uint8_t width, uint8_t height);
void ui_show_game_start(void);
void ui_show_game(void);
void ui_refresh_game(void);
void ui_show_game_over(uint16_t best_score) BANKED;
void ui_show_results(uint16_t score, uint16_t best) BANKED;
void ui_update_results(uint8_t selection) BANKED;
void ui_draw_board(void);
void ui_draw_piece_preview(void);
void ui_draw_score(void);
void ui_start_spiral(void);
void ui_tick(void);
void service_animation_input(void);
void ui_toggle_reduced_flash(void);
uint8_t ui_reduced_flash(void);
void ui_play_move(void);
void ui_play_rotate(void);
void ui_play_place(void);
void ui_play_invalid(void);

#endif
