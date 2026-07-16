"""
============================================================

AIDEA Floorplanning

Test Netlist Loader

Automatically locates the synthesized Yosys JSON netlist.

============================================================
"""

import os

from backend.floorplanning.netlist_loader import NetlistLoader


# ==========================================================
# POSSIBLE NETLIST LOCATIONS
# ==========================================================

POSSIBLE_PATHS = [

    "outputs/netlists/design.json",
    "outputs/netlists/netlist.json",
    "outputs/netlist.json",
    "outputs/yosys/netlist.json",
    "outputs/synthesis/netlist.json"

]


# ==========================================================
# FIND NETLIST
# ==========================================================

json_file = None

for path in POSSIBLE_PATHS:

    if os.path.exists(path):

        json_file = path

        break


if json_file is None:

    print("=" * 60)
    print("ERROR : No synthesized Yosys JSON netlist found.")
    print("=" * 60)

    print("\nExpected one of:\n")

    for p in POSSIBLE_PATHS:
        print("   ", p)

    print("\nPlease run synthesis first.")

    raise SystemExit(1)


print("=" * 60)
print("Using Netlist :", json_file)
print("=" * 60)


# ==========================================================
# LOAD DESIGN
# ==========================================================

loader = NetlistLoader(json_file)

design = loader.load()


# ==========================================================
# DESIGN SUMMARY
# ==========================================================

print("\n")
print("=" * 60)
print("DESIGN SUMMARY")
print("=" * 60)

print("Top Module :", design.top)

print("Number of Modules :", len(design.modules))


# ==========================================================
# MODULE DETAILS
# ==========================================================

for module in design.modules:

    print("\n--------------------------------------------")

    print("Module :", module.name)

    print("Ports :", len(module.ports))

    print("Cells :", len(module.cells))

    print("Nets  :", len(module.nets))

    print("--------------------------------------------")


print("\n")
print("=" * 60)
print("Netlist Loader Test Completed Successfully")
print("=" * 60)