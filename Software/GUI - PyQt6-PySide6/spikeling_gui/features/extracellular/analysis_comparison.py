"""One-to-one temporal agreement of events within scientific boundaries."""
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from itertools import groupby
from math import isfinite


@dataclass(frozen=True)
class EventAnchor:
    id: tuple | str
    sample: int
    tick: int
    time_ms: float
    segment: int
    epoch: int
    channel: str
    provenance: str

    @property
    def key(self):
        return self.segment, self.epoch


@dataclass(frozen=True)
class Agreement:
    pairs: tuple
    left_only: tuple
    right_only: tuple
    ambiguous_right: tuple


def validate_tolerance(tolerance_ms):
    if not isfinite(tolerance_ms) or not 0 <= tolerance_ms <= 5:
        raise ValueError("Use a matching tolerance between 0 and 5 model ms.")


def match_events(left, right, tolerance_ms, rate, cancel=None):
    """Maximise ordered match count, then minimise total absolute tick error.

    A Fenwick prefix table stores the best chain ending before a given right
    index. Each candidate edge extends the table from earlier left events only.
    """
    validate_tolerance(tolerance_ms)
    tolerance = tolerance_ms * rate / 1000 + 1e-9
    left_by_run = _by_run(left)
    right_by_run = _by_run(right)
    pairs, only_left, only_right, ambiguous = [], [], [], []
    for key in sorted(left_by_run.keys() | right_by_run.keys()):
        a = left_by_run.get(key, [])
        b = right_by_run.get(key, [])
        local_pairs, collision = _optimal_pairs(a, b, tolerance, cancel)
        if cancel is not None and cancel.is_set():
            return None
        matched_a = {i for i, _ in local_pairs}
        matched_b = {j for _, j in local_pairs}
        pairs.extend((a[i], b[j]) for i, j in local_pairs)
        only_left.extend(event for i, event in enumerate(a) if i not in matched_a)
        only_right.extend(event for j, event in enumerate(b) if j not in matched_b)
        ambiguous.extend(event for j, event in enumerate(b) if j in collision)
    return Agreement(tuple(pairs), tuple(only_left), tuple(only_right), tuple(ambiguous))


def _by_run(events):
    ordered = sorted(events, key=lambda event: (event.key, event.tick, event.id))
    return {key: list(items) for key, items in groupby(ordered, key=lambda event: event.key)}


def _optimal_pairs(left, right, tolerance, cancel):
    times = [event.tick for event in right]
    tree = [None] * (len(right) + 1)
    left_ticks = [event.tick for event in left]
    ambiguous = {j for j, tick in enumerate(times)
                 if bisect_right(left_ticks, tick + tolerance) - bisect_left(left_ticks, tick - tolerance) > 1}

    def score(node):
        return (0, 0) if node is None else node[:2]

    def best(before):
        result = None
        while before:
            candidate = tree[before]
            if score(candidate) > score(result):
                result = candidate
            before -= before & -before
        return result

    for i, event in enumerate(left):
        if cancel is not None and cancel.is_set():
            return (), ()
        lo = bisect_left(times, event.tick - tolerance)
        hi = bisect_right(times, event.tick + tolerance)
        pending = []
        for j in range(lo, hi):
            previous = best(j)
            length, negative_error = score(previous)
            pending.append((j + 1, (length + 1, negative_error - abs(event.tick - times[j]),
                                    i, j, previous)))
        for index, node in pending:
            while index < len(tree):
                if score(node) > score(tree[index]):
                    tree[index] = node
                index += index & -index
    result = []
    node = best(len(right))
    while node is not None:
        _, _, i, j, node = node
        result.append((i, j))
    return result[::-1], ambiguous
