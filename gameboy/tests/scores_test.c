#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "scores.h"

int main(void) {
    uint8_t record[SAVE_BYTES];
    uint8_t damaged[SAVE_BYTES];
    uint8_t index;
    ScoreTable decoded;
    scores_defaults();
    assert(scores_insert(0u) == SCORE_COUNT);
    assert(scores_insert(1349u) == 1u);
    assert(scores_insert(65000u) == 0u);
    assert(scores_insert(50000u) == 1u);
    assert(score_table.entries[0].score == 65000u);
    assert(score_table.entries[1].score == 50000u);
    assert(score_table.entries[2].score == 1349u);
    memcpy(score_table.entries[0].initials, "GBY", 3u);
    memcpy(score_table.entries[1].initials, "A B", 3u);
    score_table.sound = 0u;
    score_table.reduced_flash = 1u;
    score_table.generation = 65535u;
    scores_encode(record);
    assert(scores_decode(record, &decoded));
    assert(decoded.entries[0].score == 65000u);
    assert(!memcmp(decoded.entries[0].initials, "GBY", 3u));
    assert(decoded.entries[1].score == 50000u);
    assert(!memcmp(decoded.entries[1].initials, "A B", 3u));
    assert(decoded.generation == 65535u);
    assert(!decoded.sound && decoded.reduced_flash);
    for (index = 0u; index < 61u; ++index) {
        memcpy(damaged, record, SAVE_BYTES);
        damaged[index] ^= 1u;
        assert(!scores_decode(damaged, &decoded));
    }
    memcpy(damaged, record, SAVE_BYTES);
    damaged[60] = 0u;
    assert(!scores_decode(damaged, &decoded));
    puts("Score insertion, settings, CRC and incomplete-write tests passed");
    return 0;
}
