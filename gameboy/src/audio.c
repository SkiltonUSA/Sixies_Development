#include <gb/gb.h>
#include "audio.h"

uint8_t audio_enabled = 1u;
static uint8_t scene_loading;

static void audio_vblank(void) NONBANKED {
    music_tick();
}

static void audio_timer(void) NONBANKED {
    if (scene_loading) music_tick();
}

void audio_initialize(void) {
    NR52_REG = 0x80u;
    NR50_REG = 0x77u;
    NR51_REG = 0xFFu;
    add_VBL(audio_vblank);
    add_TIM(audio_timer);
    set_interrupts(VBL_IFLAG | LCD_IFLAG | TIM_IFLAG);
}

void audio_scene_load_begin(void) {
    __critical {
        scene_loading = 1u;
        TMA_REG = 188u;
        TIMA_REG = 188u;
        TAC_REG = 0x04u;
    }
}

void audio_scene_load_end(void) {
    __critical {
        TAC_REG = 0u;
        TIMA_REG = 0u;
        scene_loading = 0u;
    }
}
