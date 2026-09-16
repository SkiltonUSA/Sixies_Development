#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "game.h"

static uint8_t effect_count;

void effects_present_merge(
    uint8_t consumed_face,
    uint8_t group_count,
    uint8_t origin,
    uint8_t chain_depth,
    uint16_t award,
    uint8_t callout
) {
    (void)consumed_face;
    (void)group_count;
    (void)origin;
    (void)chain_depth;
    (void)award;
    (void)callout;
    ++effect_count;
}

static uint8_t pair_index(uint8_t first, uint8_t second) {
    if (first < 1u || first > 3u || second < 1u || second > 3u) return 0xFFu;
    return (uint8_t)((first - 1u) * 3u + second - 1u);
}

static void test_opening_probabilities(void) {
    uint32_t pairs[9];
    uint32_t singles[7];
    uint32_t sample;
    uint8_t index;

    memset(pairs, 0, sizeof(pairs));
    memset(singles, 0, sizeof(singles));
    game_new(0x6123u);
    for (sample = 0u; sample < 100000u; ++sample) {
        memset(game_state.board, 0, sizeof(game_state.board));
        game_state.four_unlocked = 0u;
        game_state.five_unlocked = 0u;
        game_spawn_piece();
        if (game_state.piece_count == 1u) {
            ++singles[game_state.piece_first];
        } else {
            index = pair_index(game_state.piece_first, game_state.piece_second);
            assert(index != 0xFFu);
            ++pairs[index];
        }
    }
    assert(singles[1] > 12000u && singles[1] < 13600u);
    assert(singles[2] > 7000u && singles[2] < 8400u);
    assert(singles[3] > 2000u && singles[3] < 3100u);
    assert(!singles[4] && !singles[5] && !singles[6]);
    assert(!pairs[pair_index(1u, 1u)] && !pairs[pair_index(2u, 2u)] && !pairs[pair_index(3u, 3u)]);
    assert(pairs[pair_index(1u, 2u)] > 12000u && pairs[pair_index(1u, 2u)] < 13600u);
    assert(pairs[pair_index(1u, 3u)] > 19500u && pairs[pair_index(1u, 3u)] < 21500u);
    assert(pairs[pair_index(2u, 1u)] > 24600u && pairs[pair_index(2u, 1u)] < 26600u);
    assert(pairs[pair_index(2u, 3u)] > 2000u && pairs[pair_index(2u, 3u)] < 3100u);
    assert(pairs[pair_index(3u, 1u)] > 9200u && pairs[pair_index(3u, 1u)] < 11300u);
    assert(pairs[pair_index(3u, 2u)] > 4300u && pairs[pair_index(3u, 2u)] < 6000u);
}

static void test_four_pressure(void) {
    uint32_t pair_three_four;
    uint32_t pair_three_three;
    uint32_t single_four;
    uint32_t sample;

    pair_three_four = 0u;
    pair_three_three = 0u;
    single_four = 0u;
    game_new(0x64A5u);
    for (sample = 0u; sample < 100000u; ++sample) {
        memset(game_state.board, 0, sizeof(game_state.board));
        game_state.board[0] = 4u;
        game_state.board[4] = 4u;
        game_state.board[20] = 4u;
        game_state.board[24] = 4u;
        game_state.four_unlocked = 0u;
        game_state.five_unlocked = 0u;
        game_spawn_piece();
        if (game_state.piece_count == 1u && game_state.piece_first == 4u) ++single_four;
        if (game_state.piece_count == 2u && game_state.piece_first == 3u && game_state.piece_second == 4u) ++pair_three_four;
        if (game_state.piece_count == 2u && game_state.piece_first == 3u && game_state.piece_second == 3u) ++pair_three_three;
    }
    assert(pair_three_four > 32000u && pair_three_four < 38000u);
    assert(single_four > 13000u && single_four < 17000u);
    assert(pair_three_three > 4000u && pair_three_three < 6000u);
}

static void test_matching_fallback_is_single(void) {
    uint8_t index;

    game_new(0x6688u);
    for (index = 0u; index < GAME_BOARD_SIZE; ++index) game_state.board[index] = 6u;
    game_state.board[0] = 0u;
    game_state.board[24] = 0u;
    game_spawn_piece();
    assert(game_state.piece_count == 1u);
}

static void prepare_single(uint8_t face, uint8_t origin) {
    game_state.piece_first = face;
    game_state.piece_second = 0u;
    game_state.piece_count = 1u;
    game_state.cursor_x = (uint8_t)(origin % GAME_BOARD_WIDTH);
    game_state.cursor_y = (uint8_t)(origin / GAME_BOARD_WIDTH);
}

static void test_chain_scoring(void) {
    game_new(0x6001u);
    memset(game_state.board, 0, sizeof(game_state.board));
    game_state.score = 0u;
    game_state.board[11] = 1u;
    game_state.board[13] = 1u;
    game_state.board[7] = 2u;
    game_state.board[17] = 2u;
    prepare_single(1u, 12u);
    effect_count = 0u;
    assert(game_place_piece());
    assert(game_state.board[12] == 3u);
    assert(game_state.score == 15u);
    assert(game_state.merge_depth == 2u);
    assert(effect_count == 2u);
}

static void test_unlocks(void) {
    game_new(0x6002u);
    memset(game_state.board, 0, sizeof(game_state.board));
    game_state.score = 0u;
    game_state.board[11] = 4u;
    game_state.board[13] = 4u;
    game_state.board[17] = 4u;
    prepare_single(4u, 12u);
    assert(game_place_piece());
    assert(game_state.four_unlocked);
    assert(game_state.board[12] == 5u);
    assert(game_state.score == 41u);

    memset(game_state.board, 0, sizeof(game_state.board));
    game_state.score = 0u;
    game_state.board[11] = 6u;
    game_state.board[13] = 6u;
    game_state.board[17] = 6u;
    prepare_single(6u, 12u);
    assert(game_place_piece());
    assert(game_state.five_unlocked);
    assert(game_state.board[12] == 0u);
    assert(game_state.score == 124u);
}

static void test_independent_five_unlock(void) {
    uint16_t sample;
    uint16_t fives = 0u;
    uint16_t pairs = 0u;
    game_new(0x1234u);
    game_state.five_unlocked = 1u;
    for (sample = 0u; sample < 10000u; ++sample) {
        game_spawn_piece();
        if (game_state.piece_count == 1u) {
            assert(game_state.piece_first != 4u);
            if (game_state.piece_first == 5u) ++fives;
        } else {
            assert(game_state.piece_second != 4u);
            if (game_state.piece_second == 5u) ++pairs;
        }
    }
    assert(fives > 400u && pairs > 900u);
    game_new(0x1234u);
    assert(!game_state.five_unlocked && !game_state.four_unlocked);
}

static void test_density_and_neighbor_weights(void) {
    uint16_t sample;
    uint16_t singles;
    uint16_t ones = 0u;
    uint8_t index;
    uint8_t occupied;
    game_new(0xAA55u);
    for (occupied = 18u; occupied <= 22u; occupied += 4u) {
        memset(game_state.board, 0, 25u);
        for (index = 0u; index < occupied; ++index) game_state.board[index] = 6u;
        singles = 0u;
        for (sample = 0u; sample < 10000u; ++sample) {
            game_spawn_piece();
            singles += game_state.piece_count == 1u;
        }
        if (occupied == 18u) assert(singles > 6000u && singles < 6500u);
        else assert(singles > 7900u && singles < 8400u);
    }
    memset(game_state.board, 6, 25u);
    game_state.board[12] = 0u;
    game_state.board[7] = game_state.board[11] = 1u;
    game_state.board[13] = 2u;
    for (sample = 0u; sample < 10000u; ++sample) {
        game_spawn_piece();
        assert(game_state.piece_count == 1u);
        assert(game_state.piece_first == 1u || game_state.piece_first == 2u);
        ones += game_state.piece_first == 1u;
    }
    assert(ones > 6400u && ones < 7000u);
}

static void test_placement_and_pair_order(void) {
    GameState snapshot;
    uint8_t orientation;
    uint8_t second;
    game_new(99u);
    game_state.piece_count = 2u;
    game_state.piece_first = game_state.piece_second = 1u;
    for (orientation = 0u; orientation < 4u; ++orientation) {
        game_state.cursor_x = game_state.cursor_y = 2u;
        game_state.orientation = orientation;
        assert(game_placement_valid(&second));
        assert(second == (orientation == 0u ? 13u : orientation == 1u ? 17u : orientation == 2u ? 11u : 7u));
        game_state.cursor_x = orientation == 0u ? 4u : 0u;
        game_state.cursor_y = orientation == 1u ? 4u : 0u;
        memcpy(&snapshot, &game_state, sizeof(snapshot));
        assert(!game_place_piece());
        assert(!memcmp(&snapshot, &game_state, sizeof(snapshot)));
    }
    game_state.cursor_x = game_state.cursor_y = 2u;
    game_state.orientation = 0u;
    game_state.board[7] = 1u;
    game_state.score = 65534u;
    assert(game_place_piece());
    assert(game_state.board[12] == 2u && !game_state.board[13]);
    assert(game_state.score == 1u && game_state.merge_depth == 1u);

    memset(game_state.board, 0, 25u);
    game_state.board[7] = game_state.board[11] = 1u;
    game_state.board[8] = game_state.board[14] = 4u;
    game_state.piece_count = 2u;
    game_state.piece_first = 1u;
    game_state.piece_second = 4u;
    game_state.score = 0u;
    assert(game_place_piece());
    assert(game_state.board[12] == 2u && game_state.board[13] == 5u);
    assert(game_state.score == 77u && game_state.merge_depth == 2u);

    memset(game_state.board, 0, 25u);
    game_state.board[6] = game_state.board[18] = 3u;
    prepare_single(3u, 12u);
    game_state.score = 0u;
    assert(game_place_piece());
    assert(game_state.board[12] == 3u && game_state.score == 0u);
}

int main(void) {
    test_opening_probabilities();
    test_four_pressure();
    test_matching_fallback_is_single();
    test_chain_scoring();
    test_unlocks();
    test_independent_five_unlock();
    test_density_and_neighbor_weights();
    test_placement_and_pair_order();
    puts("Game Boy rules tests passed");
    return 0;
}
