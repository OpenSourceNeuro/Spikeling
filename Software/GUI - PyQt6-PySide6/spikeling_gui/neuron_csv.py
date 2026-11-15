"""Shared neuron CSV schema; accept headers written by older generators."""
import csv
from math import isfinite

NEURON_COLUMNS = (
    "a", "b", "c", "d", "PhotoGain (%)", "PhotoDecay (1/ms)", "PhotoRecovery (1/ms)",
    "Syn1 Gain (%)", "Syn1 Decay (1/ms)", "Syn2 Gain (%)", "Syn2 Decay (1/ms)",
)


def read_neuron_csv(path):
    """Read the first parameter row, preserving historical multi-row behavior.

    Whitespace-insensitive header matching handles legacy generator spellings.
    Do not impose new generator exploration limits on previously saved models.
    """
    try:
        return _read_neuron_csv(path)
    except csv.Error as error:
        raise ValueError(f"Cannot read neuron CSV: {error}") from error


def _read_neuron_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as stream:
        rows = csv.reader(stream)
        headers = next(rows, [])
        normalized = ["".join(header.split()) for header in headers]
        indices = []
        for name in NEURON_COLUMNS:
            key = "".join(name.split())
            if normalized.count(key) != 1:
                raise ValueError(f"Neuron CSV must contain exactly one {name} column.")
            indices.append(normalized.index(key))
        row = next((row for row in rows if any(cell.strip() for cell in row)), None)
        if row is None:
            raise ValueError("The neuron CSV contains no parameter row.")
        try:
            parameters = tuple(float(row[index]) for index in indices)
        except (ValueError, IndexError, OverflowError) as error:
            raise ValueError("Neuron parameters must be numeric and complete.") from error
        if not all(isfinite(value) for value in parameters):
            raise ValueError("Neuron parameters must be finite numbers.")
        return parameters
