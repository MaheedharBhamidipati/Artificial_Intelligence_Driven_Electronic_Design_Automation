"""
Layered layout engine for RTL schematics.

Positions gates left-to-right in topological layers (inputs on the
left, outputs on the right), the way EDA schematic viewers conventionally
lay out combinational logic. Fixes two bugs present in the original
implementation:

1. Combinational loops through sequential elements. Any gate whose
   input, however indirectly, depends on its own output through a
   DFF/FF/REGISTER would previously never reach indegree 0 in the
   BFS-based topological sort, so the queue would drain with gates
   still unvisited — and those gates were silently dropped from the
   rendered schematic with no warning. This version detects that stall
   and breaks the cycle at a sequential-element boundary (falling back
   to the lowest-remaining-indegree node if no register is present in
   the loop), logging a warning either way, so every gate is always
   placed.
2. Gate-type-correct sizing. Dimensions now come from symbol_library
   instead of being hardcoded to a single 120x80 box for every gate
   regardless of type — symbol_library.gate_dimensions was imported in
   the original file but never actually called.
"""

import logging
from collections import defaultdict, deque
from typing import Dict, List, Tuple

from backend.schematic.symbol_library import gate_dimensions, required_height_for_inputs
from backend.schematic.ff_renderer import is_sequential_gate

logger = logging.getLogger("aidea.schematic.layout_engine")


class LayoutEngine:
    """Computes (x, y, width, height) for every gate in a netlist."""

    def __init__(self, layer_spacing: int = 320, row_spacing: int = 60,
                 margin_x: int = 250, margin_y: int = 120):
        self.layer_spacing = layer_spacing
        self.row_spacing = row_spacing
        self.margin_x = margin_x
        self.margin_y = margin_y

    # ------------------------------------------------------------------
    # MAIN
    # ------------------------------------------------------------------

    def generate_layout(self, gates: List[dict]) -> List[dict]:
        if not gates:
            return []

        gate_lookup = {g["id"]: g for g in gates}
        graph, indegree = self._build_graph(gates)
        layer_of = self._layer_gates(gates, graph, indegree)
        return self._position_gates(gate_lookup, layer_of)

    # ------------------------------------------------------------------
    # GRAPH CONSTRUCTION
    # ------------------------------------------------------------------

    def _build_graph(self, gates: List[dict]) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
        net_drivers: Dict[str, str] = {}
        for gate in gates:
            output_net = gate.get("output")
            if output_net:
                net_drivers[output_net] = gate["id"]

        graph = defaultdict(list)
        indegree: Dict[str, int] = {g["id"]: 0 for g in gates}

        for gate in gates:
            gate_id = gate["id"]
            for net in gate.get("inputs", []):
                src = net_drivers.get(net)
                if src and src != gate_id:
                    graph[src].append(gate_id)
                    indegree[gate_id] += 1

        return graph, indegree

    # ------------------------------------------------------------------
    # LAYERING (topological sort with cycle breaking)
    # ------------------------------------------------------------------

    def _layer_gates(self, gates: List[dict], graph: Dict[str, List[str]],
                      indegree: Dict[str, int]) -> Dict[str, int]:
        indegree = dict(indegree)  # local mutable copy
        gate_lookup = {g["id"]: g for g in gates}
        all_ids = [g["id"] for g in gates]

        layer_of: Dict[str, int] = {}
        queue = deque((gid, 0) for gid in all_ids if indegree.get(gid, 0) == 0)
        visited = set()

        while len(visited) < len(all_ids):
            if not queue:
                remaining = [gid for gid in all_ids if gid not in visited]
                if not remaining:
                    break

                # Prefer breaking the cycle at a sequential element —
                # that's where a real schematic would draw a feedback
                # loop closing. If the loop is purely combinational
                # (invalid RTL, but we still must not crash or drop
                # gates), break at the node with the smallest remaining
                # indegree instead.
                pick = next(
                    (gid for gid in remaining
                     if is_sequential_gate(gate_lookup[gid].get("gate_type", ""))),
                    None,
                )
                if pick is None:
                    pick = min(remaining, key=lambda gid: indegree.get(gid, 0))

                logger.warning(
                    "Feedback cycle detected; breaking at gate '%s' (type=%s) "
                    "so layout stays complete",
                    pick, gate_lookup[pick].get("gate_type"),
                )
                queue.append((pick, 0))

            gate_id, layer = queue.popleft()
            if gate_id in visited:
                continue
            visited.add(gate_id)
            layer_of[gate_id] = layer

            for neighbor in graph.get(gate_id, []):
                if neighbor in visited:
                    continue
                indegree[neighbor] = max(0, indegree.get(neighbor, 0) - 1)
                if indegree[neighbor] == 0:
                    queue.append((neighbor, layer + 1))

        return layer_of

    # ------------------------------------------------------------------
    # POSITIONING
    # ------------------------------------------------------------------

    def _position_gates(self, gate_lookup: Dict[str, dict], layer_of: Dict[str, int]) -> List[dict]:
        rows_by_layer = defaultdict(list)
        for gate_id, layer in layer_of.items():
            rows_by_layer[layer].append(gate_id)

        positioned: List[dict] = []
        for layer in sorted(rows_by_layer):
            y = self.margin_y
            for gid in rows_by_layer[layer]:
                gate = gate_lookup[gid]
                gate_type = gate.get("gate_type", "")
                num_inputs = len(gate.get("inputs", []))

                width, base_height = gate_dimensions(gate_type)
                height = max(base_height, required_height_for_inputs(gate_type, num_inputs))

                gate["x"] = self.margin_x + layer * self.layer_spacing
                gate["y"] = y
                gate["width"] = width
                gate["height"] = height

                y += height + self.row_spacing
                positioned.append(gate)

        return positioned
