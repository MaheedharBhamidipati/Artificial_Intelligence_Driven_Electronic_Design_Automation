import json
from .gate_mapper import GateMapper


class NetlistGenerator:

    def __init__(self, filepath):

        self.filepath = filepath

        self.netlist = {}

    def generate(self):

        mapper = GateMapper(self.filepath)

        gates = mapper.map_gates()

        self.netlist = {
            "design_name": self.filepath,
            "gates": gates
        }

        return self.netlist

    def save_netlist(self, filename="netlist.json"):

        with open(filename, "w") as f:
            json.dump(self.netlist, f, indent=4)

        print(f"\nNetlist saved -> {filename}")


if __name__ == "__main__":

    generator = NetlistGenerator("example.v")

    netlist = generator.generate()

    from pprint import pprint
    pprint(netlist)

    generator.save_netlist()
