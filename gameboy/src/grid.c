#include <gb/gb.h>
#include <stdint.h>

#include "grid.h"

#define GRID_LEFT 2u
#define GRID_TOP 1u
#define GRID_CELL_TILES 3u
#define GRID_CELL_COUNT 5u
#define GRID_SPAN_TILES ((GRID_CELL_TILES * GRID_CELL_COUNT) + 1u)

#define GRID_TILE_HORIZONTAL 1u
#define GRID_TILE_VERTICAL 2u
#define GRID_TILE_CROSS 3u
#define GRID_TILE_COUNT 4u

static const uint8_t grid_tiles[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,

    0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF,
    0x00, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,

    0x10, 0x38, 0x10, 0x38, 0x10, 0x38, 0x10, 0x38,
    0x10, 0x38, 0x10, 0x38, 0x10, 0x38, 0x10, 0x38,

    0x10, 0x38, 0x10, 0x38, 0x10, 0xFF, 0xFF, 0xFF,
    0x10, 0xFF, 0x10, 0x38, 0x10, 0x38, 0x10, 0x38,
};

void grid_load_tiles(void) {
    set_bkg_data(GRID_TILE_BLANK, GRID_TILE_COUNT, grid_tiles);
}

void grid_draw(void) {
    uint8_t tile_x;
    uint8_t tile_y;
    uint8_t tile_index;

    for (tile_y = 0; tile_y < GRID_SPAN_TILES; ++tile_y) {
        for (tile_x = 0; tile_x < GRID_SPAN_TILES; ++tile_x) {
            if (tile_y % GRID_CELL_TILES == 0) {
                tile_index = tile_x % GRID_CELL_TILES == 0
                    ? GRID_TILE_CROSS
                    : GRID_TILE_HORIZONTAL;
            } else if (tile_x % GRID_CELL_TILES == 0) {
                tile_index = GRID_TILE_VERTICAL;
            } else {
                tile_index = GRID_TILE_BLANK;
            }

            set_bkg_tile_xy(
                (uint8_t)(GRID_LEFT + tile_x),
                (uint8_t)(GRID_TOP + tile_y),
                tile_index
            );
        }
    }
}
