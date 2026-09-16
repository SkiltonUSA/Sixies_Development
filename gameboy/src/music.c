#include <gb/gb.h>

#include "audio.h"
#if defined(SIXIES_ENABLE_TITLE_MUSIC)
#include "hUGEDriver.h"

extern const hUGESong_t sixies_title;

#define TITLE_MUSIC_BANK 3u

static uint8_t music_active;
#endif

void music_start(void) NONBANKED {
#if defined(SIXIES_ENABLE_TITLE_MUSIC)
    uint8_t active_bank;

    if (!audio_enabled || music_active) return;
    __critical {
        active_bank = CURRENT_BANK;
        SWITCH_ROM_MBC5(TITLE_MUSIC_BANK);
        hUGE_init(&sixies_title);
        SWITCH_ROM_MBC5(active_bank);
        music_active = 1u;
    }
#endif
}

void music_stop(void) NONBANKED {
    __critical {
#if defined(SIXIES_ENABLE_TITLE_MUSIC)
        music_active = 0u;
#endif
        NR12_REG = 0u;
        NR22_REG = 0u;
        NR30_REG = 0u;
        NR42_REG = 0u;
    }
}

void music_tick(void) NONBANKED {
#if defined(SIXIES_ENABLE_TITLE_MUSIC)
    uint8_t active_bank;

    if (!music_active || !audio_enabled) return;
    active_bank = CURRENT_BANK;
    SWITCH_ROM_MBC5(TITLE_MUSIC_BANK);
    hUGE_dosound();
    SWITCH_ROM_MBC5(active_bank);
#endif
}
