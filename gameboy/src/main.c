#include <gb/gb.h>
#include "game.h"
#include "ui.h"
#include "audio.h"
#include "scores.h"
#include "generated_art.h"

#define TITLE_PROMPT_BLINK_FRAMES 30u
#define TITLE_CARD_FRAMES 660u
#define GAME_OVER_FRAMES 90u
#define CREDITS_SCROLL_FRAMES 3u
#define CREDITS_SCROLL_LIMIT 219u

uint8_t screen_state;
static uint16_t seed;
static uint8_t previous;
static uint8_t queued_action;
#if defined(SIXIES_ENABLE_CHEAT)
static uint8_t cheat_index;

static uint8_t cheat_step(uint8_t pressed) {
    static const uint8_t code[] = {
        J_UP, J_UP, J_DOWN, J_DOWN, J_LEFT,
        J_RIGHT, J_LEFT, J_RIGHT, J_B, J_A,
    };

    if (!pressed) return 0u;
    if (pressed == code[cheat_index]) {
        ++cheat_index;
        if (cheat_index == sizeof(code)) {
            cheat_index = 0u;
            return 1u;
        }
    } else {
        cheat_index = pressed == code[0] ? 1u : 0u;
    }
    return 0u;
}
#endif

static uint8_t read_pressed(void) {
    uint8_t keys;
    uint8_t pressed;
    wait_vbl_done();
    ++seed;
    keys = joypad();
    pressed = keys & (uint8_t)~previous;
    previous = keys;
    return pressed;
}

static void release_buttons(void) {
    do {
        read_pressed();
    } while (previous);
}

void service_animation_input(void) {
    uint8_t keys;
    uint8_t pressed;
    if (screen_state != 4u) return;
    keys = joypad();
    pressed = keys & (uint8_t)~previous;
    previous = keys;
    if (pressed & J_B) queued_action = J_B;
    else if (pressed & J_LEFT) queued_action = J_LEFT;
    else if (pressed & J_RIGHT) queued_action = J_RIGHT;
    else if (pressed & J_UP) queued_action = J_UP;
    else if (pressed & J_DOWN) queued_action = J_DOWN;
}

static void instructions(void) {
    uint8_t page = 0u;
    uint8_t pressed;
    screen_state = 3u;
    ui_show_instructions(page);
    release_buttons();
    for (;;) {
        pressed = read_pressed();
        if (pressed & (J_A | J_START | J_B)) break;
        if (pressed & J_RIGHT) {
            page = (page + 1u) % ART_INSTRUCTION_PAGES;
            ui_update_instructions(page);
        } else if (pressed & J_LEFT) {
            page = (page + ART_INSTRUCTION_PAGES - 1u) % ART_INSTRUCTION_PAGES;
            ui_update_instructions(page);
        }
    }
    release_buttons();
}

static void startup_intro(void) {
    uint16_t elapsed = 0u;
    uint8_t pressed;
    screen_state = 9u;
    ui_show_intro();
    release_buttons();
    do {
        pressed = read_pressed();
        ++elapsed;
    } while (elapsed < 240u && !(pressed & (J_A | J_START)));
    release_buttons();
}

static void attract(void) {
    uint8_t card = 0u;
    uint8_t pressed;
    uint8_t prompt_frames = TITLE_PROMPT_BLINK_FRAMES;
    uint8_t prompt_visible = 1u;
    uint8_t credits_frames = CREDITS_SCROLL_FRAMES;
    uint8_t credits_scroll = 0u;
    uint16_t elapsed = 0u;
    screen_state = 0u;
    ui_show_title(score_table.entries[0].score);
    music_start();
    release_buttons();
    for (;;) {
        pressed = read_pressed();
        ++elapsed;
        if (pressed & (J_A | J_START)) break;
        if (card == 1u) {
            if (pressed & (J_LEFT | J_RIGHT)) ui_turn_score_page();
            ui_tick_scores();
        }
        if (card == 0u) {
            --prompt_frames;
            if (!prompt_frames) {
                prompt_frames = TITLE_PROMPT_BLINK_FRAMES;
                prompt_visible ^= 1u;
                ui_set_title_prompt(prompt_visible);
            }
        }
        if (card == 2u) {
            --credits_frames;
            if (!credits_frames) {
                credits_frames = CREDITS_SCROLL_FRAMES;
                if (credits_scroll < CREDITS_SCROLL_LIMIT) ++credits_scroll;
            }
            ui_scroll_credits(credits_scroll);
        }
        if ((pressed & J_B) || elapsed >= (card == 0u ? TITLE_CARD_FRAMES : card == 2u ? 660u : 300u)) {
            card = (pressed & J_B) ? (card == 2u ? 0u : 2u) : (card + 1u) % 3u;
            screen_state = card;
            elapsed = 0u;
            if (card == 0u) {
                prompt_frames = TITLE_PROMPT_BLINK_FRAMES;
                prompt_visible = 1u;
                ui_show_title(score_table.entries[0].score);
            }
            else if (card == 1u) ui_show_scores(SCORE_COUNT, 0u);
            else {
                credits_frames = CREDITS_SCROLL_FRAMES;
                credits_scroll = 0u;
                ui_show_credits();
            }
        }
    }
    music_stop();
}

static void settings_menu(void) {
    uint8_t selected = 0u;
    uint8_t pressed;
    uint8_t enabled;
    uint8_t changed;

    screen_state = 12u;
    ui_show_settings(selected);
    release_buttons();
    for (;;) {
        pressed = read_pressed();
        if (pressed & (J_B | J_START)) break;
        if (pressed & (J_UP | J_DOWN)) selected ^= 1u;
        if (pressed & (J_LEFT | J_RIGHT)) {
            enabled = (pressed & J_LEFT) ? 0u : 1u;
            changed = 0u;
            if (selected == 0u) {
                if (audio_enabled != enabled) {
                    audio_enabled = enabled;
                    score_table.sound = audio_enabled;
                    changed = 1u;
                }
            } else if (ui_reduced_flash() != (uint8_t)!enabled) {
                ui_set_reduced_flash((uint8_t)!enabled);
                changed = 1u;
            }
            if (changed) storage_save();
        }
        if (pressed) ui_update_settings(selected);
    }
    release_buttons();
}

static uint8_t start_menu(void) {
    uint8_t selected = 0u;
    uint8_t pressed;

    screen_state = 11u;
    ui_show_start_menu(selected);
    release_buttons();
    for (;;) {
        pressed = read_pressed();
        if (pressed & J_B) { release_buttons(); return 0u; }
        if (pressed & J_UP) selected = (selected + 3u) % 4u;
        if (pressed & J_DOWN) selected = (selected + 1u) % 4u;
        if (pressed & (J_UP | J_DOWN)) {
            ui_play_move();
            ui_update_start_menu(selected);
        }
        if (pressed & (J_A | J_START)) {
            if (selected == 0u) { release_buttons(); return 1u; }
            if (selected == 1u) settings_menu();
            else if (selected == 2u) instructions();
            else {
                screen_state = 1u;
                ui_show_menu_scores();
                release_buttons();
                do {
                    pressed = read_pressed();
                    if (pressed & (J_LEFT | J_RIGHT)) ui_turn_score_page();
                    ui_tick_scores();
                } while (!(pressed & (J_A | J_B | J_START)));
                release_buttons();
            }
            screen_state = 11u;
            ui_show_start_menu(selected);
            release_buttons();
        }
    }
}

static uint8_t pause_game(void) {
    uint8_t selected = 0u;
    uint8_t pressed;
    screen_state = 5u;
    ui_show_pause(selected);
    release_buttons();
    for (;;) {
        pressed = read_pressed();
        if (pressed & (J_B | J_START)) break;
        if (pressed & J_UP) selected = (selected + 4u) % 5u;
        if (pressed & J_DOWN) selected = (selected + 1u) % 5u;
        if (pressed & J_A) {
            if (selected == 0u) break;
            if (selected == 1u) { instructions(); screen_state = 5u; ui_show_pause(selected); }
            if (selected == 2u) {
                audio_enabled ^= 1u;
                score_table.sound = audio_enabled;
                storage_save();
            }
            if (selected == 3u) { ui_toggle_reduced_flash(); storage_save(); }
            if (selected == 4u) {
                screen_state = 8u;
                ui_show_confirm();
                release_buttons();
                do { pressed = read_pressed(); } while (!(pressed & (J_A | J_B)));
                if (pressed & J_A) { release_buttons(); return 1u; }
                screen_state = 5u;
                ui_show_pause(selected);
            }
        }
        if (pressed) ui_update_pause(selected);
    }
    release_buttons();
    return 0u;
}

static void enter_initials(uint8_t rank) {
    uint8_t letter = 0u;
    uint8_t pressed;
    char *initial;
    release_buttons();
    screen_state = 7u;
    ui_show_scores(rank, letter);
    for (;;) {
        pressed = read_pressed();
        if (pressed & J_START) break;
        if (pressed & J_LEFT) letter = (letter + 2u) % 3u;
        if (pressed & J_RIGHT) letter = (letter + 1u) % 3u;
        initial = &score_table.entries[rank].initials[letter];
        if (pressed & J_UP) *initial = *initial == 'Z' ? 'A' : *initial + 1;
        if (pressed & J_DOWN) *initial = *initial == 'A' ? 'Z' : *initial - 1;
        if (pressed & J_B) letter = (letter + 2u) % 3u;
        if (pressed & J_A) {
            if (letter == 2u) break;
            ++letter;
        }
        if (pressed) ui_update_initials(rank, letter);
    }
    storage_save();
    release_buttons();
}

static uint8_t finish_game(void) {
    uint8_t rank;
    uint8_t pressed;
    uint8_t frames;
    uint8_t selected = 0u;
    uint16_t best = score_table.entries[0].score;

    screen_state = 6u;
    ui_show_game_over(best);
    for (frames = 0u; frames < GAME_OVER_FRAMES; ++frames) {
        pressed = read_pressed();
        if (pressed & (J_A | J_B)) break;
    }
    if (game_state.score > best) best = game_state.score;
    screen_state = 10u;
    ui_show_results(game_state.score, best);
    release_buttons();
    for (;;) {
        pressed = read_pressed();
        if (pressed & J_B) { selected = 1u; break; }
        if (pressed & (J_UP | J_DOWN)) {
            selected ^= 1u;
            ui_update_results(selected);
        }
        if (pressed & (J_A | J_START)) break;
    }
    rank = scores_insert(game_state.score);
    if (rank < SCORE_COUNT) enter_initials(rank);
    release_buttons();
    return selected == 0u;
}

static uint8_t play_game(void) {
    uint8_t pressed;
    game_new(seed ^ DIV_REG);
#if defined(SIXIES_ENABLE_CHEAT)
    cheat_index = 0u;
#endif
    queued_action = 0u;
    screen_state = 4u;
    ui_show_game_start();
    ui_start_spiral();
    service_animation_input();
    for (;;) {
        if (queued_action) {
            pressed = queued_action;
            queued_action = 0u;
        } else pressed = read_pressed();
        ui_tick();
#if defined(SIXIES_ENABLE_CHEAT)
        if (cheat_step(pressed)) return finish_game();
#endif
        if (pressed & J_START) {
            if (pause_game()) return 1u;
            screen_state = 4u;
            ui_show_game();
            continue;
        }
        if (pressed & J_LEFT) game_move_cursor(-1, 0);
        else if (pressed & J_RIGHT) game_move_cursor(1, 0);
        else if (pressed & J_UP) game_move_cursor(0, -1);
        else if (pressed & J_DOWN) game_move_cursor(0, 1);
        if (pressed & (J_LEFT | J_RIGHT | J_UP | J_DOWN)) {
            ui_play_move();
            ui_draw_board();
            ui_draw_piece_preview();
        }
        if (pressed & J_B) {
            game_rotate_piece();
            ui_play_rotate();
            ui_refresh_game();
        }
        if (pressed & J_A) {
            if (!game_placement_valid(0)) ui_play_invalid();
            else {
                ui_play_place();
                game_place_piece();
                service_animation_input();
                if (game_state.game_over) return finish_game();
                ui_refresh_game();
            }
        }
    }
}

void main(void) {
    storage_load();
    audio_enabled = score_table.sound;
    ui_initialize();
    audio_initialize();
    seed = DIV_REG | 0x600u;
    startup_intro();
    for (;;) {
        attract();
        while (start_menu()) {
            while (play_game()) {}
        }
    }
}
