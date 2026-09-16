#!/usr/bin/env python3
"""Validate platform-neutral Sixies gameplay vectors.

This is deliberately a small, dependency-free reference model. It mirrors the
ordering in src/grid_base.asm and is intended to be easy to port to C tests.
"""

import json
import sys
from pathlib import Path


BOARD_WIDTH = 5
BOARD_CELLS = 25
OFFSETS = ((1, 0), (0, 1), (-1, 0), (0, -1))
JOYSTICK_STATES = {
    "neutral": 0x1F,
    "left": 0x1B,
    "right": 0x17,
    "up": 0x1E,
    "down": 0x1D,
    "fire": 0x0F,
    "fire_left": 0x0B,
    "fire_right": 0x07,
}
KEYBOARD_ACTIONS = {
    "Q": "rotate_left",
    "E": "rotate_right",
}
DEAL_WEIGHTS = (
    ((1,), 5),
    ((2,), 3),
    ((3,), 1),
    ((1, 2), 5),
    ((1, 3), 8),
    ((2, 1), 10),
    ((2, 3), 1),
    ((3, 1), 4),
    ((3, 2), 2),
)
DEAL_TABLE = tuple(deal for deal, weight in DEAL_WEIGHTS for _ in range(weight))
DEAL_WEIGHT_TOTAL = 39
ACCEPTED_RNG_MAX = 234
NEIGHBOR_BONUS_RNG_MAX = 250
FOUR_PROMOTION_RNG_MAX = 240


def flatten(rows):
    if len(rows) != BOARD_WIDTH or any(len(row) != BOARD_WIDTH for row in rows):
        raise ValueError("board must contain five rows of five cells")
    board = [cell for row in rows for cell in row]
    if any(not isinstance(cell, int) or cell < 0 or cell > 6 for cell in board):
        raise ValueError("board cells must be integers from 0 through 6")
    return board


def rows(board):
    return [board[start : start + BOARD_WIDTH] for start in range(0, BOARD_CELLS, BOARD_WIDTH)]


def index_at(x, y):
    return y * BOARD_WIDTH + x


def neighbor(index, orientation):
    x = index % BOARD_WIDTH
    y = index // BOARD_WIDTH
    dx, dy = OFFSETS[orientation]
    x += dx
    y += dy
    if x < 0 or x >= BOARD_WIDTH or y < 0 or y >= BOARD_WIDTH:
        return None
    return index_at(x, y)


def placement(board, count, origin, orientation):
    x, y = origin
    if x < 0 or x >= BOARD_WIDTH or y < 0 or y >= BOARD_WIDTH:
        return False, None, None
    first = index_at(x, y)
    second = None if count == 1 else neighbor(first, orientation)
    if board[first] != 0 or (count == 2 and second is None):
        return False, first, second
    if count == 2 and board[second] != 0:
        return False, first, second
    return True, first, second


def find_group(board, active):
    value = board[active]
    if value == 0:
        return []
    queue = [active]
    visited = {active}
    group = []
    while queue:
        current = queue.pop(0)
        group.append(current)
        # C64 traversal order is left, right, up, down.
        for direction in (2, 0, 3, 1):
            candidate = neighbor(current, direction)
            if candidate is not None and candidate not in visited and board[candidate] == value:
                visited.add(candidate)
                queue.append(candidate)
    return group


CHAIN_MULTIPLIERS = (1, 2, 5, 10, 20, 40)


def chain_multiplier(chain_depth):
    return CHAIN_MULTIPLIERS[min(chain_depth, len(CHAIN_MULTIPLIERS)) - 1]


def resolve(board, active, score, chain_depth=0):
    events = []
    while board[active] != 0:
        group = find_group(board, active)
        if len(group) < 3:
            break
        value = board[active]
        chain_depth += 1
        delta = 3 * value * chain_multiplier(chain_depth)
        if value == 6:
            delta += 150
        score = min(9999, score + delta)
        events.append({"value": value, "count": len(group), "score_delta": delta, "active": active})
        for cell in group:
            board[cell] = 0
        if value == 6:
            break
        board[active] = value + 1
    return score, events


def place_piece(board, values, origin, orientation, score):
    count = len(values)
    valid, first, second = placement(board, count, origin, orientation)
    if not valid:
        return False, score, []
    board[first] = values[0]
    if count == 2:
        board[second] = values[1]
    score, events = resolve(board, first, score)
    if count == 2 and board[second] != 0:
        score, second_events = resolve(board, second, score, len(events))
        events.extend(second_events)
    return True, score, events


def random_byte(seed):
    shifted = (seed << 1) & 0xFF
    if seed & 0x80:
        shifted ^= 0x1D
    return shifted


def double_space_available(board):
    for cell, value in enumerate(board):
        if value != 0:
            continue
        for direction in (0, 1):
            other = neighbor(cell, direction)
            if other is not None and board[other] == 0:
                return True
    return False


def any_placement(board, count):
    orientations = range(1) if count == 1 else range(4)
    for orientation in orientations:
        for y in range(BOARD_WIDTH):
            for x in range(BOARD_WIDTH):
                if placement(board, count, (x, y), orientation)[0]:
                    return True
    return False


def neighbor_match_candidates(board):
    candidates = []
    for cell, value in enumerate(board):
        if value == 0:
            continue
        if any(
            other is not None and board[other] == 0
            for other in (neighbor(cell, direction) for direction in range(4))
        ):
            candidates.append(value)
    return candidates


def random_modulo(seed, modulus, accepted_max):
    while True:
        seed = random_byte(seed)
        if seed <= accepted_max:
            return (seed - 1) % modulus, seed


def spawn(board, seed, previous_singles_only=False):
    # This condition is derived fresh for every piece. The previous value is
    # accepted only for vector compatibility and must never latch the state.
    singles_only = not double_space_available(board)
    while True:
        seed = random_byte(seed)
        if seed <= ACCEPTED_RNG_MAX:
            deal = DEAL_TABLE[(seed - 1) % DEAL_WEIGHT_TOTAL]
            if not singles_only or len(deal) == 1:
                break
    count = len(deal)
    value0 = deal[0]
    value1 = deal[1] if count == 2 else 0

    if 0 in board and 5 in board:
        visible_values = [value0] if count == 1 else [value0, value1]
        if 2 in visible_values:
            promotion_roll, seed = random_modulo(
                seed, 20, FOUR_PROMOTION_RNG_MAX
            )
            if promotion_roll == 6:
                if value0 == 2:
                    value0 = 4
                else:
                    value1 = 4

    if singles_only:
        candidates = neighbor_match_candidates(board)
        if candidates:
            bonus_roll, seed = random_modulo(seed, 10, NEIGHBOR_BONUS_RNG_MAX)
            if bonus_roll == 0:
                candidate_max = (255 // len(candidates)) * len(candidates)
                candidate_index, seed = random_modulo(
                    seed, len(candidates), candidate_max
                )
                value0 = candidates[candidate_index]

    return {
        "count": count,
        "raw_values": [value0, value1],
        "cursor": [2, 2],
        "orientation": 0,
        "seed": seed,
        "singles_only": singles_only,
        "game_over": not any_placement(board, count),
    }


def joystick_sequence(states, piece_count):
    latch = 0
    fire_state = 0
    actions = []
    for name in states:
        joystick = JOYSTICK_STATES[name]
        action = "none"
        if (joystick & 0x10) == 0:
            if fire_state == 0:
                fire_state = 1
            if piece_count == 2 and (joystick & 0x04) == 0:
                if latch == 0:
                    latch = 1
                    fire_state = 2
                    action = "rotate_left"
            elif piece_count == 2 and (joystick & 0x08) == 0:
                if latch == 0:
                    latch = 1
                    fire_state = 2
                    action = "rotate_right"
            else:
                latch = 0
        elif fire_state != 0:
            previous_fire_state = fire_state
            fire_state = 0
            if previous_fire_state == 1:
                action = "place"
        elif (joystick & 0x1F) == 0x1F:
            latch = 0
        elif latch == 0:
            latch = 1
            if (joystick & 0x04) == 0:
                action = "left"
            elif (joystick & 0x08) == 0:
                action = "right"
            elif (joystick & 0x01) == 0:
                action = "up"
            elif (joystick & 0x02) == 0:
                action = "down"
        actions.append(action)
    return {"actions": actions, "latch": latch, "fire_state": fire_state}


def keyboard_sequence(keys):
    return {"actions": [KEYBOARD_ACTIONS.get(key, "none") for key in keys]}


def new_game_confirmation(keys):
    waiting = False
    new_game = False
    actions = []
    for key in keys:
        if not waiting:
            if key == "N":
                waiting = True
                actions.append("prompt")
            else:
                actions.append("none")
        elif key == "Y":
            waiting = False
            new_game = True
            actions.append("confirm")
        elif key == "N":
            waiting = False
            actions.append("cancel")
        else:
            actions.append("waiting")
    return {"actions": actions, "waiting": waiting, "new_game": new_game}


def check_equal(vector_id, field, actual, expected, failures):
    if actual != expected:
        failures.append(f"{vector_id}: {field}: expected {expected!r}, got {actual!r}")


def validate(data):
    failures = []
    count = 0
    for vector in data["vectors"]:
        count += 1
        vector_id = vector["id"]
        operation = vector["operation"]
        expected = vector["expected"]
        board = None if operation in (
            "joystick_sequence",
            "keyboard_sequence",
            "new_game_confirmation",
        ) else flatten(vector["board"])

        if operation == "placement":
            piece = vector["piece"]
            result = placement(board, len(piece["values"]), tuple(piece["origin"]), piece["orientation"])
            check_equal(vector_id, "valid", result[0], expected["valid"], failures)
            check_equal(vector_id, "origin_index", result[1], expected["origin_index"], failures)
            check_equal(vector_id, "second_index", result[2], expected["second_index"], failures)
        elif operation == "resolve":
            score, events = resolve(board, vector["active"], vector.get("score", 0))
            check_equal(vector_id, "board", rows(board), expected["board"], failures)
            check_equal(vector_id, "score", score, expected["score"], failures)
            check_equal(vector_id, "events", events, expected["events"], failures)
        elif operation == "place":
            piece = vector["piece"]
            valid, score, events = place_piece(
                board, piece["values"], tuple(piece["origin"]), piece["orientation"], vector.get("score", 0)
            )
            check_equal(vector_id, "valid", valid, expected["valid"], failures)
            check_equal(vector_id, "board", rows(board), expected["board"], failures)
            check_equal(vector_id, "score", score, expected["score"], failures)
            check_equal(vector_id, "events", events, expected["events"], failures)
        elif operation == "spawn":
            result = spawn(board, vector["seed"], vector.get("singles_only", False))
            check_equal(vector_id, "spawn", result, expected, failures)
        elif operation == "space_detection":
            result = {
                "double_space_available": double_space_available(board),
                "single_placement_available": any_placement(board, 1),
                "double_placement_available": any_placement(board, 2),
            }
            check_equal(vector_id, "space_detection", result, expected, failures)
        elif operation == "neighbor_candidates":
            result = neighbor_match_candidates(board)
            check_equal(vector_id, "neighbor_candidates", result, expected, failures)
        elif operation == "joystick_sequence":
            result = joystick_sequence(vector["states"], vector["piece_count"])
            check_equal(vector_id, "joystick_sequence", result, expected, failures)
        elif operation == "keyboard_sequence":
            result = keyboard_sequence(vector["keys"])
            check_equal(vector_id, "keyboard_sequence", result, expected, failures)
        elif operation == "new_game_confirmation":
            result = new_game_confirmation(vector["keys"])
            check_equal(vector_id, "new_game_confirmation", result, expected, failures)
        else:
            failures.append(f"{vector_id}: unknown operation {operation!r}")
    return count, failures


def main():
    vector_path = Path(__file__).with_name("gameplay-vectors.json")
    if len(sys.argv) > 1:
        vector_path = Path(sys.argv[1])
    with vector_path.open(encoding="utf-8") as stream:
        data = json.load(stream)
    count, failures = validate(data)
    if failures:
        print("\n".join(failures), file=sys.stderr)
        print(f"FAILED: {len(failures)} mismatches in {count} vectors", file=sys.stderr)
        return 1
    print(f"PASS: {count} Sixies gameplay vectors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
