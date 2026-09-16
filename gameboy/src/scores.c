#include <string.h>
#include "scores.h"

ScoreTable score_table;
static const ScoreEntry defaults[SCORE_COUNT] = {
    {{'D','O','M'}, 1349u}, {{'P','R','I'}, 1020u},
    {{'T','W','D'}, 893u}, {{'T','A','N'}, 802u},
    {{'T','B',' '}, 755u}, {{'A','C','E'}, 650u},
    {{'M','A','X'}, 540u}, {{'Z','E','D'}, 430u},
    {{'B','O','T'}, 320u}, {{'C','P','U'}, 210u}
};

static uint16_t checksum(const uint8_t *record) {
    uint16_t crc = 0xFFFFu;
    uint8_t index;
    uint8_t bit;
    for (index = 0u; index < 58u; ++index) {
        crc ^= (uint16_t)record[index] << 8;
        for (bit = 0u; bit < 8u; ++bit) crc = (crc & 0x8000u) ? (uint16_t)((crc << 1) ^ 0x1021u) : (uint16_t)(crc << 1);
    }
    return crc;
}

void scores_defaults(void) {
    memcpy(score_table.entries, defaults, sizeof(defaults));
    score_table.sound = 1u;
    score_table.reduced_flash = 0u;
    score_table.generation = 0u;
}

uint8_t scores_insert(uint16_t score) {
    uint8_t rank;
    uint8_t index;
    for (rank = 0u; rank < SCORE_COUNT; ++rank) {
        if (score > score_table.entries[rank].score) {
            for (index = SCORE_COUNT - 1u; index > rank; --index) score_table.entries[index] = score_table.entries[index - 1u];
            memcpy(score_table.entries[rank].initials, "AAA", 3u);
            score_table.entries[rank].score = score;
            return rank;
        }
    }
    return SCORE_COUNT;
}

void scores_encode(uint8_t *record) {
    uint8_t index;
    uint8_t offset;
    uint16_t crc;
    memset(record, 0, SAVE_BYTES);
    memcpy(record, "S6GB", 4u);
    record[4] = 1u;
    record[5] = (uint8_t)score_table.generation;
    record[6] = (uint8_t)(score_table.generation >> 8);
    record[7] = score_table.sound | (score_table.reduced_flash << 1);
    for (index = 0u; index < SCORE_COUNT; ++index) {
        offset = 8u + index * 5u;
        memcpy(record + offset, score_table.entries[index].initials, 3u);
        record[offset + 3u] = (uint8_t)score_table.entries[index].score;
        record[offset + 4u] = (uint8_t)(score_table.entries[index].score >> 8);
    }
    crc = checksum(record);
    record[58] = (uint8_t)crc;
    record[59] = (uint8_t)(crc >> 8);
    record[60] = 0xA5u;
}

uint8_t scores_decode(const uint8_t *record, ScoreTable *table) {
    uint8_t index;
    uint8_t letter;
    uint8_t offset;
    uint16_t crc;
    if (memcmp(record, "S6GB", 4u) || record[4] != 1u || record[60] != 0xA5u || record[7] > 3u) return 0u;
    crc = checksum(record);
    if ((uint8_t)crc != record[58] || (uint8_t)(crc >> 8) != record[59]) return 0u;
    table->generation = record[5] | ((uint16_t)record[6] << 8);
    table->sound = record[7] & 1u;
    table->reduced_flash = (record[7] >> 1) & 1u;
    for (index = 0u; index < SCORE_COUNT; ++index) {
        offset = 8u + index * 5u;
        for (letter = 0u; letter < 3u; ++letter) {
            char value = (char)record[offset + letter];
            if (value != ' ' && (value < 'A' || value > 'Z')) return 0u;
            table->entries[index].initials[letter] = value;
        }
        table->entries[index].score = record[offset + 3u] | ((uint16_t)record[offset + 4u] << 8);
        if (index && table->entries[index].score > table->entries[index - 1u].score) return 0u;
    }
    return 1u;
}
