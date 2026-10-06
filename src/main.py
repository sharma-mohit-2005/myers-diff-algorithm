"""
Assignment 1 - Myers' diff
    python main.py lines A B       Part A: minimal line diff
    python main.py highlight A B   Part B: line diff + changed characters
"""

import sys
from array import array


def read_lines(path):
    with open(path, "rb") as file:       # bytes, so b"\r" stays in the line
        lines = file.read().split(b"\n")
    if lines[-1] == b"":                 # a final newline is not an extra line
        lines.pop()
    return lines


def myers(old_seq, new_seq):
    """Shortest edit script from old_seq to new_seq, as a list of ' ', '-', '+'.

    Names follow the paper: x = position in old_seq, y = position in new_seq,
    d = number of edits so far, k = x - y (the diagonal).
    """
    old_len, new_len = len(old_seq), len(new_seq)
    if old_len == 0 or new_len == 0:
        return ['-'] * old_len + ['+'] * new_len

    k_offset = old_len + new_len + 1     # k can be negative, so k is stored at k + k_offset
    furthest_x = [0] * (2 * k_offset + 1)    # the V array: furthest x reached on diagonal k
    history = []                         # history[d] = furthest_x for k = -d..d after step d

    for d in range(old_len + new_len + 1):
        for k in range(-d, d + 1, 2):
            if k == -d or (k != d and furthest_x[k - 1 + k_offset] < furthest_x[k + 1 + k_offset]):
                x = furthest_x[k + 1 + k_offset]         # down from k+1: insert
            else:
                x = furthest_x[k - 1 + k_offset] + 1     # right from k-1: delete
            y = x - k
            while x < old_len and y < new_len and old_seq[x] == new_seq[y]:   # snake: equal items are free
                x += 1
                y += 1
            furthest_x[k + k_offset] = x
            if x >= old_len and y >= new_len:
                break
        history.append(array('i', furthest_x[k_offset - d: k_offset + d + 1]))
        if x >= old_len and y >= new_len:
            break

    # Walk back from (old_len, new_len) to (0, 0) with the same choice rule.
    edit_script = []
    for d in range(len(history) - 1, 0, -1):
        prev_furthest_x = history[d - 1]     # diagonal k is at index k + shift
        shift = d - 1
        k = x - y
        if k == -d or (k != d and prev_furthest_x[k - 1 + shift] < prev_furthest_x[k + 1 + shift]):
            prev_k = k + 1
        else:
            prev_k = k - 1
        prev_x = prev_furthest_x[prev_k + shift]
        prev_y = prev_x - prev_k
        while x > prev_x and y > prev_y:         # the snake, backwards
            x, y = x - 1, y - 1
            edit_script.append(' ')
        edit_script.append('+' if x == prev_x else '-')
        x, y = prev_x, prev_y
    edit_script += [' '] * x             # step d = 0 is only a snake
    edit_script.reverse()
    return edit_script


def line_diff(old_lines, new_lines):
    """A line that never appears in the other file is surely a delete or
    an insert, so Myers runs only on the other lines. Still minimal."""
    old_line_set, new_line_set = set(old_lines), set(new_lines)
    shared_script = myers([line for line in old_lines if line in new_line_set],
                          [line for line in new_lines if line in old_line_set])

    edit_script, old_index, new_index = [], 0, 0     # put the removed lines back in place
    for op in shared_script:
        while old_index < len(old_lines) and old_lines[old_index] not in new_line_set:
            edit_script.append('-')
            old_index += 1
        while new_index < len(new_lines) and new_lines[new_index] not in old_line_set:
            edit_script.append('+')
            new_index += 1
        edit_script.append(op)
        if op != '+':
            old_index += 1
        if op != '-':
            new_index += 1
    return (edit_script + ['-'] * (len(old_lines) - old_index)
            + ['+'] * (len(new_lines) - new_index))


def to_ranges(positions):
    """[3, 4, 5, 9] -> "3-6,9-10", and [] -> "." """
    if not positions:
        return "."
    range_texts, range_start = [], positions[0]
    for position, next_position in zip(positions, positions[1:] + [None]):
        if next_position != position + 1:    # the range ends at this position
            range_texts.append(f"{range_start}-{position + 1}")
            range_start = next_position
    return ",".join(range_texts)


def highlight_line(old_line, new_line):
    """Myers on the characters (code points) of two lines."""
    old_changed, new_changed, old_index, new_index = [], [], 0, 0
    for op in myers(old_line.decode("utf-8", "replace"), new_line.decode("utf-8", "replace")):
        if op == '-':
            old_changed.append(old_index)
        if op == '+':
            new_changed.append(new_index)
        if op != '+':
            old_index += 1
        if op != '-':
            new_index += 1
    return f"? {to_ranges(old_changed)} | {to_ranges(new_changed)}"


def build_output(old_lines, new_lines, edit_script, with_highlight):
    output_chunks, old_index, new_index, script_index = [], 0, 0, 0
    while script_index < len(edit_script):
        if edit_script[script_index] == ' ':
            output_chunks.append(b" " + old_lines[old_index] + b"\n")
            old_index, new_index, script_index = old_index + 1, new_index + 1, script_index + 1
            continue
        deleted_lines, inserted_lines = [], []   # one change block
        while script_index < len(edit_script) and edit_script[script_index] != ' ':
            if edit_script[script_index] == '-':
                deleted_lines.append(old_lines[old_index])
                old_index += 1
            else:
                inserted_lines.append(new_lines[new_index])
                new_index += 1
            script_index += 1
        output_chunks += [b"-" + line + b"\n" for line in deleted_lines]     # deletes first
        for pair_index, line in enumerate(inserted_lines):
            output_chunks.append(b"+" + line + b"\n")
            if with_highlight and pair_index < len(deleted_lines):   # n-th '+' pairs with n-th '-'
                ranges_line = highlight_line(deleted_lines[pair_index], line)
                output_chunks.append(ranges_line.encode() + b"\n")
    return b"".join(output_chunks)


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("lines", "highlight"):
        print("usage: main.py lines|highlight A B", file=sys.stderr)
        sys.exit(2)
    try:
        old_lines, new_lines = read_lines(sys.argv[2]), read_lines(sys.argv[3])
    except OSError as error:
        print("error:", error, file=sys.stderr)
        sys.exit(2)
    edit_script = line_diff(old_lines, new_lines)
    with_highlight = sys.argv[1] == "highlight"
    sys.stdout.buffer.write(build_output(old_lines, new_lines, edit_script, with_highlight))


if __name__ == "__main__":
    main()
