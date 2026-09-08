#include <gb/gb.h>
#include <gb/cgb.h>

#include "grid.h"

static const palette_color_t game_palette[] = {
    RGB8(224, 248, 208),
    RGB8(136, 192, 112),
    RGB8(52, 104, 86),
    RGB8(8, 24, 32),
};

void main(void) {
    DISPLAY_OFF;

    if (_cpu == CGB_TYPE) {
        set_bkg_palette(BKGF_CGB_PAL0, 1, game_palette);
    } else {
        BGP_REG = DMG_PALETTE(DMG_WHITE, DMG_LITE_GRAY, DMG_DARK_GRAY, DMG_BLACK);
    }

    fill_bkg_rect(0, 0, 20, 18, GRID_TILE_BLANK);
    grid_load_tiles();
    grid_draw();

    SHOW_BKG;
    DISPLAY_ON;

    while (1) {
        wait_vbl_done();
    }
}
