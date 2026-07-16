"""
Orthogonal (Manhattan-style) wire router.

The original implementation drew every input wire as a straight stub at
a fixed offset from its own gate (`gx - 100`), with no reference to
where the actual driving gate was — so wires only lined up with their
source by coincidence, and any circuit with more than one layer showed
visibly disconnected-looking wiring. This version routes each net from
the real driving gate's output pin to each real consuming gate's input
pin.

Routing strategy: each net is drawn as an orthogonal path through a
per-net vertical "channel", with parallel nets between the same pair of
gates offset into separate lanes so they fan out instead of stacking
exactly on top of one another. This is not a full maze router (no hard
collision detection against gate bodies), but lane offsetting removes
the majority of overlap seen with naive straight-line routing.

Feedback nets — any consumer whose x position is at or before its
driver's x position, which happens for combinational loops closed
through a register — are routed around the layout through a return
channel below the lowest gate, the conventional way schematic tools
draw feedback without cutting straight through blocks.
"""

from collections import defaultdict
from typing import Dict, List, Tuple

from backend.schematic.symbol_library import input_pin_positions, output_pin_position
from backend.schematic.bus_router import is_bus

Point = Tuple[int, int]


class WireRouter:

    def __init__(self, lane_pitch: int = 10, return_margin: int = 60, stub_length: int = 60):
        self.lane_pitch = lane_pitch
        self.return_margin = return_margin
        self.stub_length = stub_length

    def generate_wires(self, gates: List[dict]) -> List[dict]:
        if not gates:
            return []

        gate_lookup = {g["id"]: g for g in gates}
        net_drivers = self._map_net_drivers(gates)
        driven_nets = {net for g in gates for net in g.get("inputs", [])}
        max_y = max((g["y"] + g["height"] for g in gates), default=0)
        return_channel_y = max_y + self.return_margin

        wires: List[dict] = []
        lane_counter: Dict[Tuple[str, str], int] = defaultdict(int)

        for gate in gates:
            gate_id = gate["id"]
            inputs = gate.get("inputs", [])
            pins = input_pin_positions(gate.get("gate_type", ""), len(inputs))

            for idx, net in enumerate(inputs):
                dest_pin = pins[idx] if idx < len(pins) else (0, gate["height"] // 2)
                dest = (gate["x"] + dest_pin[0], gate["y"] + dest_pin[1])

                driver_id = net_drivers.get(net)
                if driver_id is None or driver_id not in gate_lookup or driver_id == gate_id:
                    # Primary input, or an undriven net — stub in from the left
                    # rather than dropping the wire silently.
                    src = (dest[0] - self.stub_length, dest[1])
                    wires.append(self._make_wire(net, [src, dest], is_feedback=False))
                    continue

                driver = gate_lookup[driver_id]
                out_pin = output_pin_position(driver.get("gate_type", ""))
                src = (driver["x"] + out_pin[0], driver["y"] + out_pin[1])

                lane_key = (driver_id, gate_id)
                lane_counter[lane_key] += 1
                lane_offset = lane_counter[lane_key] * self.lane_pitch

                is_feedback = src[0] >= dest[0]
                points = (
                    self._route_feedback(src, dest, return_channel_y, lane_offset)
                    if is_feedback
                    else self._route_forward(src, dest, lane_offset)
                )
                wires.append(self._make_wire(net, points, is_feedback=is_feedback))

            # Dangling output (drives nothing downstream) still deserves a
            # visible pin stub rather than being invisible.
            output_net = gate.get("output")
            if output_net and output_net not in driven_nets:
                out_pin = output_pin_position(gate.get("gate_type", ""))
                src = (gate["x"] + out_pin[0], gate["y"] + out_pin[1])
                dest = (src[0] + self.stub_length, src[1])
                wires.append(self._make_wire(output_net, [src, dest], is_feedback=False))

        return wires

    # ------------------------------------------------------------------

    def _map_net_drivers(self, gates: List[dict]) -> Dict[str, str]:
        return {g["output"]: g["id"] for g in gates if g.get("output")}

    def _route_forward(self, src: Point, dest: Point, lane_offset: int) -> List[Point]:
        mid_x = (src[0] + dest[0]) // 2 + lane_offset
        return [src, (mid_x, src[1]), (mid_x, dest[1]), dest]

    def _route_feedback(self, src: Point, dest: Point, channel_y: int, lane_offset: int) -> List[Point]:
        drop_x = src[0] + 20 + lane_offset
        rise_x = dest[0] - 20 - lane_offset
        y = channel_y + lane_offset
        return [
            src,
            (drop_x, src[1]),
            (drop_x, y),
            (rise_x, y),
            (rise_x, dest[1]),
            dest,
        ]

    def _make_wire(self, signal: str, points: List[Point], is_feedback: bool) -> dict:
        return {
            "signal": signal,
            "points": points,
            "is_bus": is_bus(signal),
            "is_feedback": is_feedback,
            # First/last point kept for backward compatibility with any
            # code still expecting the old flat x1/y1/x2/y2 schema.
            "x1": points[0][0], "y1": points[0][1],
            "x2": points[-1][0], "y2": points[-1][1],
        }
