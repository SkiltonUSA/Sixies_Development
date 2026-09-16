#ifndef SIXIES_SCORES_H
#define SIXIES_SCORES_H
#include <stdint.h>

#define SCORE_COUNT 10u
#define SAVE_BYTES 64u
typedef struct ScoreEntry {
    char initials[3];
    uint16_t score;
} ScoreEntry;
typedef struct ScoreTable {
    ScoreEntry entries[SCORE_COUNT];
    uint8_t sound;
    uint8_t reduced_flash;
    uint16_t generation;
} ScoreTable;
extern ScoreTable score_table;
void scores_defaults(void);
uint8_t scores_insert(uint16_t score);
void scores_encode(uint8_t *record);
uint8_t scores_decode(const uint8_t *record, ScoreTable *table);
void storage_load(void);
void storage_save(void);
#endif
