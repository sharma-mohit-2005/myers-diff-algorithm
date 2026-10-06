"""
Assignment 1 - Myers' diff

    python main.py lines A B       Part A: minimal line diff of A -> B
    python main.py highlight A B   Part B: the same diff + changed characters

The diff is found with Myers' O(ND) algorithm (1986), so it always has
the fewest possible deletions + insertions.
"""

import sys
from array import array


# ---------------------------------------------------------------
# Reading a file
# ---------------------------------------------------------------

def read_lines(path):
    """Read the file as raw bytes and split it on b'\\n'.
    A final newline does not make an extra empty line.
    Any b'\\r' stays inside the line."""
    with open(path, "rb") as f:
        data = f.read()
    lines = data.split(b"\n")
    if lines[-1] == b"":
        lines.pop()
    return lines


# ---------------------------------------------------------------
# Myers algorithm
# ---------------------------------------------------------------
# Works on any two sequences a and b (lists of lines, or strings).
# Returns the edit script as a list of single characters:
#   ' '  keep    (item is in a and b)
#   '-'  delete  (item is only in a)
#   '+'  insert  (item is only in b)

def diff(a, b):
    n = len(a)
    m = len(b)

    # Equal items at the start and the end are always "keep".
    # Cutting them off first makes big files with few changes fast.
    start = 0
    while start < n and start < m and a[start] == b[start]:
        start += 1
    end = 0
    while end < n - start and end < m - start and a[n - 1 - end] == b[m - 1 - end]:
        end += 1

    middle = myers(a[start:n - end], b[start:m - end])
    return [' '] * start + middle + [' '] * end


def myers(a, b):
    n = len(a)
    m = len(b)
    if n == 0:
        return ['+'] * m
    if m == 0:
        return ['-'] * n

    max_d = n + m
    offset = max_d + 1      # k can be negative, so v[k] is stored at v[k + offset]

    # v[k + offset] = furthest x reached so far on diagonal k  (k = x - y)
    v = [0] * (2 * max_d + 3)

    # trace[d] = the part of v for k = -d .. d, saved after step d.
    # It is stored as an array of C ints to keep the memory small.
    trace = []

    for d in range(max_d + 1):
        for k in range(-d, d + 1, 2):
            # Choose the previous diagonal:
            #   from k+1 by moving down  -> insert (x stays the same)
            #   from k-1 by moving right -> delete (x goes up by one)
            if k == -d or (k != d and v[k - 1 + offset] < v[k + 1 + offset]):
                x = v[k + 1 + offset]
            else:
                x = v[k - 1 + offset] + 1
            y = x - k

            # Snake: follow equal items along the diagonal, they cost nothing.
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1

            v[k + offset] = x

            if x >= n and y >= m:   # reached the bottom-right corner
                break

        trace.append(array('i', v[offset - d: offset + d + 1]))

        if x >= n and y >= m:
            return backtrack(trace, n, m)

    return []   # never reached, d = n + m is always enough


def backtrack(trace, n, m):
    """Start at (n, m) and walk back to (0, 0) one step d at a time,
    using the saved v values to see where each step came from."""
    x = n
    y = m
    script = []     # built from the end, reversed at the end

    for d in range(len(trace) - 1, 0, -1):
        # v as it was after step d-1. It holds k = -(d-1) .. (d-1),
        # so diagonal k is found at index k + shift.
        prev = trace[d - 1]
        shift = d - 1
        k = x - y

        # the same choice rule as in the forward pass
        if k == -d or (k != d and prev[k - 1 + shift] < prev[k + 1 + shift]):
            prev_k = k + 1
        else:
            prev_k = k - 1

        prev_x = prev[prev_k + shift]
        prev_y = prev_x - prev_k

        # the snake of this step: equal items
        while x > prev_x and y > prev_y:
            x -= 1
            y -= 1
            script.append(' ')

        # the single edit of this step
        if x == prev_x:
            script.append('+')      # moved down
        else:
            script.append('-')      # moved right

        x = prev_x
        y = prev_y

    # step d = 0 is only a snake from (0, 0)
    script.extend([' '] * x)

    script.reverse()
    return script


def deletes_first(script):
    """Inside every change block (a run of '-' and '+' with no ' '
    between them) put all '-' before all '+'. The number of edits
    does not change, so the diff stays minimal."""
    result = []
    i = 0
    while i < len(script):
        if script[i] == ' ':
            result.append(' ')
            i += 1
            continue
        deletes = 0
        inserts = 0
        while i < len(script) and script[i] != ' ':
            if script[i] == '-':
                deletes += 1
            else:
                inserts += 1
            i += 1
        result.extend(['-'] * deletes)
        result.extend(['+'] * inserts)
    return result


# ---------------------------------------------------------------
# Part A - line diff
# ---------------------------------------------------------------

def line_diff(lines_a, lines_b):
    """Returns the edit script for the two files, deletes first."""
    # Give every different line a number, so comparing two lines
    # is just comparing two small integers.
    numbers = {}
    a = [numbers.setdefault(line, len(numbers)) for line in lines_a]
    b = [numbers.setdefault(line, len(numbers)) for line in lines_b]

    # A line that never appears in the other file can never be "keep",
    # so it is surely a delete (or an insert). Take those lines out
    # before running Myers (git does the same). Fewer lines and fewer
    # edits left for Myers, and the result is still minimal.
    in_a = set(a)
    in_b = set(b)
    keep_a = [x in in_b for x in a]
    keep_b = [y in in_a for y in b]
    small_a = [x for x in a if x in in_b]
    small_b = [y for y in b if y in in_a]

    small_script = diff(small_a, small_b)

    # Put the removed lines back into the script at their places.
    script = []
    i = 0
    j = 0
    for op in small_script:
        while i < len(a) and not keep_a[i]:
            script.append('-')
            i += 1
        while j < len(b) and not keep_b[j]:
            script.append('+')
            j += 1
        script.append(op)
        if op != '+':
            i += 1
        if op != '-':
            j += 1
    script.extend(['-'] * (len(a) - i))     # only removed lines are left
    script.extend(['+'] * (len(b) - j))

    return deletes_first(script)


# ---------------------------------------------------------------
# Part B - changed character ranges
# ---------------------------------------------------------------

def to_ranges(positions):
    """[3, 4, 5, 9] -> "3-6,9". Touching positions are merged.
    No positions -> "." """
    if not positions:
        return "."
    parts = []
    first = positions[0]
    last = positions[0]
    for p in positions[1:]:
        if p == last + 1:
            last = p
        else:
            parts.append(str(first) + "-" + str(last + 1))
            first = p
            last = p
    parts.append(str(first) + "-" + str(last + 1))
    return ",".join(parts)


def highlight_line(old_line, new_line):
    """Returns the '? old | new' line for one pair of changed lines."""
    old = old_line.decode("utf-8", errors="replace")
    new = new_line.decode("utf-8", errors="replace")

    # a Python str is indexed by code point, so one emoji = one character
    script = diff(old, new)

    old_changed = []    # positions deleted from the old line
    new_changed = []    # positions inserted into the new line
    i = 0
    j = 0
    for op in script:
        if op == ' ':
            i += 1
            j += 1
        elif op == '-':
            old_changed.append(i)
            i += 1
        else:
            new_changed.append(j)
            j += 1

    return "? " + to_ranges(old_changed) + " | " + to_ranges(new_changed)


# ---------------------------------------------------------------
# Printing the output
# ---------------------------------------------------------------

def build_output(lines_a, lines_b, script, with_highlight):
    out = []
    i = 0       # position in file A
    j = 0       # position in file B
    pos = 0     # position in the script

    while pos < len(script):
        if script[pos] == ' ':
            out.append(b" " + lines_a[i] + b"\n")
            i += 1
            j += 1
            pos += 1
            continue

        # one change block: some '-' then some '+'
        deleted = []
        while pos < len(script) and script[pos] == '-':
            deleted.append(lines_a[i])
            i += 1
            pos += 1
        inserted = []
        while pos < len(script) and script[pos] == '+':
            inserted.append(lines_b[j])
            j += 1
            pos += 1

        for line in deleted:
            out.append(b"-" + line + b"\n")
        for t in range(len(inserted)):
            out.append(b"+" + inserted[t] + b"\n")
            # the t-th '+' is paired with the t-th '-', if there is one
            if with_highlight and t < len(deleted):
                out.append(highlight_line(deleted[t], inserted[t]).encode() + b"\n")

    return b"".join(out)


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("lines", "highlight"):
        print("usage: main.py lines|highlight A B", file=sys.stderr)
        sys.exit(2)

    command = sys.argv[1]
    try:
        lines_a = read_lines(sys.argv[2])
        lines_b = read_lines(sys.argv[3])
    except OSError as error:
        print("error: cannot read file:", error, file=sys.stderr)
        sys.exit(2)

    script = line_diff(lines_a, lines_b)
    output = build_output(lines_a, lines_b, script, command == "highlight")
    sys.stdout.buffer.write(output)


if __name__ == "__main__":
    main()
