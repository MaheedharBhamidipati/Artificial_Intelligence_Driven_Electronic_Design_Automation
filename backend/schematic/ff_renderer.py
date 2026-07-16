"""
Helpers specific to sequential elements (flip-flops, latches, registers).

Kept separate from symbol_library's generic pin geometry so
sequential-only concerns (which input is the clock, cycle-breaking
eligibility) don't leak into combinational-gate handling.
"""

from typing import Iterable, Set

_SEQUENTIAL_TYPES = {"DFF", "FF", "REGISTER", "LATCH"}
_CLOCK_NAMES = {"clk", "clock"}
_RESET_NAMES = {"rst", "reset", "rst_n", "arst", "arst_n", "nrst"}


def is_sequential_gate(gate_type: str) -> bool:
    return (gate_type or "").upper() in _SEQUENTIAL_TYPES


def sequential_gate_ids(gates: Iterable[dict]) -> Set[str]:
    """IDs of all sequential gates in a gate list. Used by the layout
    engine to decide where combinational feedback loops are allowed to
    be broken (at a register boundary, matching how a schematic would
    conventionally show a feedback path)."""
    return {g["id"] for g in gates if is_sequential_gate(g.get("gate_type", ""))}


def clock_input_index(gate: dict) -> int:
    """Index into gate['inputs'] that represents the clock pin, or -1
    if the gate has no inputs. Convention: a net literally named 'clk'
    or 'clock' is preferred; otherwise the last input is assumed to be
    the clock, matching common netlist emission order for sequential
    cells."""
    inputs = gate.get("inputs", [])
    for i, net in enumerate(inputs):
        base = net.split("[")[0].lower()
        if base in _CLOCK_NAMES:
            return i
    return len(inputs) - 1 if inputs else -1


def reset_input_index(gate: dict) -> int:
    """Index of a reset pin, if present, else -1."""
    inputs = gate.get("inputs", [])
    for i, net in enumerate(inputs):
        base = net.split("[")[0].lower()
        if base in _RESET_NAMES:
            return i
    return -1
