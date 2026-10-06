"""
Assignment 1 - Myers' diff
    python main.py lines A B       Part A: minimal line diff
    python main.py highlight A B   Part B: line diff + changed characters
"""

import sys
from array import array


def read_lines(path):
    with open(path, "rb") as f:          # bytes, so b"\r" stays in the line
        lines = f.read().split(b"\n")
    if lines[-1] == b"":                 # a final newline is not an extra line
        lines.pop()
    return lines


def myers(a, b):
    """Shortest edit script from a to b, as a list of ' ', '-', '+'."""
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return ['-'] * n + ['+'] * m

    offset = n + m + 1                   # k can be negative, so k is stored at k + offset
    v = [0] * (2 * offset + 1)           # v[k + offset] = furthest x on diagonal k = x - y
    trace = []                           # trace[d] = v for k = -d..d after step d

    for d in range(n + m + 1):
        for k in range(-d, d + 1, 2):
            if k == -d or (k != d and v[k - 1 + offset] < v[k + 1 + offset]):
                x = v[k + 1 + offset]            # down from k+1: insert
            else:
                x = v[k - 1 + offset] + 1        # right from k-1: delete
            y = x - k
            while x < n and y < m and a[x] == b[y]:   # snake: equal items are free
                x += 1
                y += 1
            v[k + offset] = x
            if x >= n and y >= m:
                break
        trace.append(array('i', v[offset - d: offset + d + 1]))
        if x >= n and y >= m:
            break

    # Walk back from (n, m) to (0, 0) with the same choice rule.
    script = []
    for d in range(len(trace) - 1, 0, -1):
        prev = trace[d - 1]              # diagonal k is at index k + s
        s = d - 1
        k = x - y
        if k == -d or (k != d and prev[k - 1 + s] < prev[k + 1 + s]):
            prev_k = k + 1
        else:
            prev_k = k - 1
        prev_x = prev[prev_k + s]
        prev_y = prev_x - prev_k
        while x > prev_x and y > prev_y:         # the snake, backwards
            x, y = x - 1, y - 1
            script.append(' ')
        script.append('+' if x == prev_x else '-')
        x, y = prev_x, prev_y
    script += [' '] * x                  # step d = 0 is only a snake
    script.reverse()
    return script


def line_diff(a, b):
    """A line that never appears in the other file is surely a delete or
    an insert, so Myers runs only on the other lines. Still minimal."""
    in_a, in_b = set(a), set(b)
    small = myers([x for x in a if x in in_b], [y for y in b if y in in_a])

    script, i, j = [], 0, 0              # put the removed lines back in place
    for op in small:
        while i < len(a) and a[i] not in in_b:
            script.append('-')
            i += 1
        while j < len(b) and b[j] not in in_a:
            script.append('+')
            j += 1
        script.append(op)
        if op != '+':
            i += 1
        if op != '-':
            j += 1
    return script + ['-'] * (len(a) - i) + ['+'] * (len(b) - j)


def to_ranges(positions):
    """[3, 4, 5, 9] -> "3-6,9-10", and [] -> "." """
    if not positions:
        return "."
    parts, start = [], positions[0]
    for p, q in zip(positions, positions[1:] + [None]):
        if q != p + 1:                   # the range ends at p
            parts.append(f"{start}-{p + 1}")
            start = q
    return ",".join(parts)


def highlight_line(old, new):
    """Myers on the characters (code points) of two lines."""
    old_pos, new_pos, i, j = [], [], 0, 0
    for op in myers(old.decode("utf-8", "replace"), new.decode("utf-8", "replace")):
        if op == '-':
            old_pos.append(i)
        if op == '+':
            new_pos.append(j)
        if op != '+':
            i += 1
        if op != '-':
            j += 1
    return f"? {to_ranges(old_pos)} | {to_ranges(new_pos)}"


def build_output(a, b, script, highlight):
    out, i, j, pos = [], 0, 0, 0
    while pos < len(script):
        if script[pos] == ' ':
            out.append(b" " + a[i] + b"\n")
            i, j, pos = i + 1, j + 1, pos + 1
            continue
        dels, ins = [], []               # one change block
        while pos < len(script) and script[pos] != ' ':
            if script[pos] == '-':
                dels.append(a[i])
                i += 1
            else:
                ins.append(b[j])
                j += 1
            pos += 1
        out += [b"-" + line + b"\n" for line in dels]    # deletes first
        for t, line in enumerate(ins):
            out.append(b"+" + line + b"\n")
            if highlight and t < len(dels):              # t-th '+' pairs with t-th '-'
                out.append(highlight_line(dels[t], line).encode() + b"\n")
    return b"".join(out)


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("lines", "highlight"):
        print("usage: main.py lines|highlight A B", file=sys.stderr)
        sys.exit(2)
    try:
        a, b = read_lines(sys.argv[2]), read_lines(sys.argv[3])
    except OSError as error:
        print("error:", error, file=sys.stderr)
        sys.exit(2)
    script = line_diff(a, b)
    sys.stdout.buffer.write(build_output(a, b, script, sys.argv[1] == "highlight"))


if __name__ == "__main__":
    main()
