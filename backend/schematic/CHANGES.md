# Schematic Pipeline — Production Hardening Changelog

All 10 files were reviewed and rewritten. Below is what was actually
broken, and what changed, file by file. Verified end-to-end against a
synthetic netlist containing a fan-out, an 8-bit bus, a 3-input gate,
and a DFF-closed combinational feedback loop (see `test_pipeline.py`).

## Bugs fixed (these produced wrong or missing output before)

1. **Gates silently disappeared from the schematic.**
   `layout_engine.py`'s topological sort (Kahn's algorithm) had no
   handling for cycles. Any gate whose input depended, even indirectly,
   on its own output through a DFF/register would never reach
   indegree 0 — the BFS queue would drain and those gates just never
   got a position, with no error or warning. Sequential feedback loops
   are completely normal RTL (any counter, FSM, or accumulator has
   one), so this wasn't an edge case, it was routine input silently
   producing incomplete diagrams.
   **Fix:** when the queue stalls, detect it and break the cycle at a
   sequential-element boundary (or lowest-indegree node if no register
   is present), log a warning, and continue. Every gate is now
   guaranteed a position.

2. **Wires didn't actually connect to their drivers.**
   `wire_router.py` computed wire endpoints from `gx - 100` / `gx + 80`
   relative to the *consuming* gate only — it never looked up where the
   driving gate actually was. In a single-layer circuit this looked
   fine by coincidence; in anything with 2+ layers, wires visually
   didn't reach the gates that were supposedly driving them.
   **Fix:** wires are now routed from the real driver's output pin to
   the real consumer's input pin, using actual pin coordinates from
   `symbol_library`.

3. **`svg_interactive.add_metadata` crashed on port-only gates.**
   It indexed `gate["gate_id"]`, `gate["output"]`, `gate["inputs"]`
   directly with no `.get()` — a primary input/output port gate
   (no inputs, or no output) raised `KeyError` and would have aborted
   the entire render.
   **Fix:** all lookups use `.get()` with sane defaults.

4. **Custom metadata attributes silently failed to attach.**
   Found during testing: svgwrite's default attribute validator
   rejects `data-*` attributes outright (raises `ValueError`), so the
   original interactive-metadata feature never actually worked even
   though the code "ran" (the original `add_metadata` had no error
   handling, so this would have crashed the whole render the first
   time it was exercised).
   **Fix:** `Drawing(..., debug=False)` disables the strict validator;
   `add_metadata` also now catches and logs failures instead of
   propagating them.

5. **Every gate rendered as an identical 80×40 blue box.**
   `layout_engine.py` imported `gate_dimensions` from
   `symbol_library.py` but never called it — it hardcoded
   `gate["width"] = 120; gate["height"] = 80` for literally every gate
   type. `svg_renderer.py` then hardcoded `size=(80, 40)` again,
   independently, ignoring even that. A DFF and a 2-input AND gate
   rendered as the same box.
   **Fix:** `layout_engine.py` and `svg_renderer.py` both now call
   `symbol_library.gate_dimensions()` / `gate_color()`, and gate height
   also scales up automatically for gates with many input pins
   (`required_height_for_inputs`).

6. **Canvas silently clipped anything bigger than 1600×1200.**
   `svg_renderer.py` hardcoded `size=("1600px", "1200px")` regardless
   of the actual circuit size. Any netlist with enough gates/layers to
   exceed that would just render off-canvas with no error.
   **Fix:** canvas size is now computed from the real extents of all
   positioned gates and routed wires, plus a margin.

7. **`bus_router.is_bus()` was a bare substring check.**
   `"[" in signal and "]" in signal` — true for a single indexed bit
   like `sel[2]`, and would also match malformed strings. There was no
   way to get a bus's actual width or base name anywhere in the
   codebase.
   **Fix:** proper regex parsing (`bus_router.parse_bus`,
   `bus_router.bus_width`) distinguishing a real range (`data[7:0]`)
   from a single bit index (`addr[3]`), with a `BusInfo` dataclass.
   Wire routing and rendering now use this to draw buses thicker and
   in a distinct color.

8. **`schematic_engine.py` had a hardcoded Windows dev path.**
   The `__main__` block pointed at
   `D:\AI_EDA_TOOL\backend\rtl_parser_engine\example.v` — this would
   fail immediately on any non-Windows machine or any other developer's
   checkout. The `sys.path` setup also used a somewhat fragile
   `os.path.join(dirname(__file__), "..")` pattern.
   **Fix:** takes the Verilog file as a CLI argument
   (`python schematic_engine.py path/to/file.v -o output.svg`), uses
   `pathlib` throughout, and resolves the backend root deterministically
   via `Path(__file__).resolve().parents[1]`.

## Structural / production-readiness improvements

- **Logging everywhere**, not just print statements — every module logs
  through the standard `logging` module with a consistent
  `aidea.schematic.*` logger namespace, matching the convention already
  used in `schematic_generator.py`.
- **Type hints and docstrings** on every public function/class,
  explaining *why* a piece of logic exists (especially the cycle-
  breaking and pin-geometry code, which isn't self-evident from the
  code alone).
- **`ff_renderer.py`** now does real work: `clock_input_index()` and
  `reset_input_index()` identify which input pin is the clock/reset by
  net-name convention, which the wire router / future renderer can use
  to draw clock triangles or dashed reset lines instead of a generic
  numbered input.
- **`symbol_library.py`** now provides pin *geometry*
  (`input_pin_positions`, `output_pin_position`, `clock_pin_position`),
  not just box dimensions — this is what makes real driver-to-consumer
  wire routing possible at all.
- **`color_config.py`** expanded from 6 flat constants to a per-gate-type
  color map (`gate_color()`) plus a `Theme` dataclass, so sequential
  elements, buses, and feedback wires are now visually distinguishable
  instead of everything being the same blue/green.
- **`schematic_generator.py`** (the Yosys/Graphviz pipeline) was already
  the most production-ready file here — job isolation, timeouts,
  size caps, TTL cleanup were all already present. Only light hardening
  added: PNG render failures are now logged instead of silently
  discarded, and it now shares the same interactivity-metadata
  injection (`svg_interactive.inject_interactivity`) as the custom
  renderer, so both pipelines produce SVGs with the same click/hover
  hooks for the frontend.

## What was intentionally NOT changed

- **`schematic_generator.py`'s overall architecture** (Yosys → dot →
  Graphviz `-Tsvg`) is sound and was left as the primary recommended
  path for arbitrary/complex RTL — it's more battle-tested than a
  from-scratch layout engine. `schematic_engine.py`'s custom pipeline
  is positioned as the path to use when you want AIDEA's own gate
  symbols/styling rather than Graphviz's default look.
- **Wire routing is still not a full maze router** — it does per-net
  lane offsetting to reduce overlap, not hard collision detection
  against gate bodies. For genuinely dense schematics this is the next
  thing worth investing in, but it's a meaningfully harder problem
  (proper channel routing / A* around obstacles) that's worth scoping
  as its own task rather than bundling in here.

## How to verify

```
pip install svgwrite --break-system-packages
python3 test_pipeline.py
```

This exercises the full `LayoutEngine → WireRouter → SVGRenderer` chain
against a netlist with a fan-out, an 8-bit bus, a 3-input gate, and a
DFF-closed feedback loop, and asserts no gates are dropped.
