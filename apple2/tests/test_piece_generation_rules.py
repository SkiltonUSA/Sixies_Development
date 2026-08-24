#!/usr/bin/env python3

from pathlib import Path
import re
import unittest


SOURCE = (Path(__file__).parents[1] / "src" / "main.c").read_text(encoding="ascii")


def array_values(name: str) -> tuple[int, ...]:
    match = re.search(
        rf"static const unsigned char {name}\[.*?\] = \{{(?P<body>.*?)\}};",
        SOURCE,
        re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"array not found: {name}")
    return tuple(int(value) for value in re.findall(r"\d+", match.group("body")))


def generation_source() -> str:
    start = SOURCE.index("static void generate_piece(")
    end = SOURCE.index("static void reset_piece_position(", start)
    return SOURCE[start:end]


def surrounding_source() -> str:
    start = SOURCE.index("static unsigned char weighted_surrounding_face(")
    end = SOURCE.index("static void generate_piece(", start)
    return SOURCE[start:end]


class PieceGenerationRuleTests(unittest.TestCase):
    def test_pair_pool_contains_only_approved_combinations(self) -> None:
        pairs = tuple(
            zip(
                array_values("pair_piece_first"),
                array_values("pair_piece_second"),
            )
        )

        self.assertEqual(
            pairs,
            ((1, 2), (1, 3), (2, 3), (2, 4), (3, 3), (3, 4)),
        )
        self.assertNotIn(5, array_values("pair_piece_first"))
        self.assertNotIn(5, array_values("pair_piece_second"))

    def test_single_four_unlocks_at_three_board_fours(self) -> None:
        generation = generation_source()

        self.assertIn("four_unlocked = count_value(4) >= 3", generation)
        self.assertIn("four_unlocked && choice == 3", generation)
        self.assertIn("*first = 4;", generation)

    def test_single_five_unlocks_at_four_board_fives(self) -> None:
        generation = generation_source()

        self.assertIn("five_unlocked = count_value(5) >= 4", generation)
        self.assertIn("3 + four_unlocked + five_unlocked", generation)
        self.assertIn("*first = 5;", generation)

    def test_single_mode_only_uses_the_unlocked_single_pool(self) -> None:
        generation = generation_source()
        single_branch = generation.index("if (single_mode || (rand() % 3) == 0)")
        pair_branch = generation.index(
            "    } else {\n"
            "        choice = (unsigned char) (rand() % PAIR_PIECE_COUNT);",
            single_branch,
        )

        self.assertIn("*count = 1;", generation[single_branch:pair_branch])
        self.assertIn("*second = 0;", generation[single_branch:pair_branch])
        self.assertIn("*count = 2;", generation[pair_branch:])
        self.assertIn("pair_piece_first[choice]", generation[pair_branch:])
        self.assertIn("pair_piece_second[choice]", generation[pair_branch:])

    def test_pairs_have_two_thirds_probability_during_normal_play(self) -> None:
        generation = generation_source()

        self.assertIn("single_mode || (rand() % 3) == 0", generation)

    def test_single_mode_follows_current_pair_space(self) -> None:
        generation = generation_source()

        self.assertIn("single_mode = !has_adjacent_empty_pair();", generation)
        self.assertNotIn(
            "if (!single_mode && !has_adjacent_empty_pair())",
            SOURCE,
        )
        self.assertNotIn("single_mode = 1;", SOURCE)

    def test_forced_single_mode_biases_two_thirds_toward_neighbors(self) -> None:
        generation = generation_source()

        self.assertIn("single_mode && (rand() % 3) != 0", generation)
        self.assertIn(
            "weighted_surrounding_face(four_unlocked, five_unlocked)",
            generation,
        )
        self.assertIn("if (*first != 0)", generation)

    def test_surrounding_weights_use_all_orthogonal_empty_neighbors(self) -> None:
        surrounding = surrounding_source()

        self.assertIn("direction < 4", surrounding)
        self.assertIn("orient_dx[direction]", surrounding)
        self.assertIn("orient_dy[direction]", surrounding)
        self.assertIn("board_value(", surrounding)
        self.assertEqual(surrounding.count("++weights[value - 1u];"), 1)

    def test_surrounding_bias_respects_unlocked_faces(self) -> None:
        surrounding = surrounding_source()

        self.assertIn("value > 5", surrounding)
        self.assertIn("value == 4 && !four_unlocked", surrounding)
        self.assertIn("value == 5 && !five_unlocked", surrounding)


if __name__ == "__main__":
    unittest.main()
