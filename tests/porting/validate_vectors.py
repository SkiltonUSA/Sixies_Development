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


def resolve(board, active, score):
    events = []
    while board[active] != 0:
        group = find_group(board, active)
        if len(group) < 3:
            break
        value = board[active]
        delta = len(group) * value
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
        score, second_events = resolve(board, second, score)
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


def spawn(board, seed, singles_only):
    seed = random_byte(seed)
    count = (seed & 1) + 1
    seed = random_byte(seed)
    value0 = (seed & 3) + 1
    seed = random_byte(seed)
    value1 = (seed & 3) + 1

    if sum(value == 5 for value in board) >= 5:
        seed = random_byte(seed)
        if (seed & 0x0F) == 0:
            if count == 2:
                seed = random_byte(seed)
                if seed & 1:
                    value1 = 5
                else:
                    value0 = 5
            else:
                value0 = 5

    if count == 2 and value0 == 4 and value1 == 4:
        while True:
            seed = random_byte(seed)
            raw = seed & 3
            if raw != 3:
                value1 = raw + 1
                break

    if singles_only or not double_space_available(board):
        singles_only = True
        count = 1

    return {
        "count": count,
        "raw_values": [value0, value1],
        "cursor": [2, 2],
        "orientation": 0,
        "seed": seed,
        "singles_only": singles_only,
        "game_over": not any_placement(board, count),
    }


def check_equal(vector_id, field, actual, expected, failures):
    if actual != expected:
        failures.append(f"{vector_id}: {field}: expected {expected!r}, got {actual!r}")


def validate(data):
    failures = []
    count = 0
    for vector in data["vectors"]:
        count += 1
        vector_id = vector["id"]
        board = flatten(vector["board"])
        operation = vector["operation"]
        expected = vector["expected"]

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
