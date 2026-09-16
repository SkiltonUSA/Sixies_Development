#include <gb/gb.h>
#include "scores.h"

static uint8_t slot;
static uint8_t record[SAVE_BYTES];

void storage_load(void) {
    ScoreTable candidate;
    volatile uint8_t *source;
    uint8_t index;
    uint8_t current;
    uint8_t valid = 0u;
    scores_defaults();
    ENABLE_RAM;
    SWITCH_RAM(0u);
    for (current = 0u; current < 2u; ++current) {
        source = (volatile uint8_t *)(0xA100u + (uint16_t)current * 128u);
        for (index = 0u; index < SAVE_BYTES; ++index) record[index] = source[index];
        if (scores_decode(record, &candidate) && (!valid || (int16_t)(candidate.generation - score_table.generation) > 0)) {
            score_table = candidate;
            slot = current;
            valid = 1u;
        }
    }
    source = (volatile uint8_t *)0xA000u;
    if (!valid && source[0] == 'S' && source[1] == '6') {
        uint8_t rank = scores_insert(source[2] | ((uint16_t)source[3] << 8));
        if (rank < SCORE_COUNT) {
            score_table.entries[rank].initials[0] = 'O';
            score_table.entries[rank].initials[1] = 'L';
            score_table.entries[rank].initials[2] = 'D';
        }
    }
    DISABLE_RAM;
}

void storage_save(void) {
    volatile uint8_t *destination;
    uint8_t index;
    ++score_table.generation;
    scores_encode(record);
    slot ^= 1u;
    destination = (volatile uint8_t *)(0xA100u + (uint16_t)slot * 128u);
    ENABLE_RAM;
    SWITCH_RAM(0u);
    destination[60] = 0u;
    for (index = 0u; index < 60u; ++index) destination[index] = record[index];
    destination[60] = record[60];
    DISABLE_RAM;
}
