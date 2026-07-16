
from pyverilog.vparser.parser import parse


class RTLParser:

    def __init__(self, filepath):

        self.filepath = filepath

        self.ast = None

        self.modules = []

    # =====================================================
    # PARSE FILE
    # =====================================================
    def parse_file(self):

        ast, _ = parse([self.filepath])

        self.ast = ast

        return ast

    # =====================================================
    # SAFE ADD
    # =====================================================
    def safe_add(self, target_list, value):

        if value and value not in target_list:

            target_list.append(value)

    # =====================================================
    # WIDTH EXTRACTOR
    # =====================================================
    def get_width(self, node):

        if hasattr(node, "width") and node.width:

            try:

                msb = int(node.width.msb.value)
                lsb = int(node.width.lsb.value)

                return abs(msb - lsb) + 1

            except:

                return "UNKNOWN"

        return 1

    # =====================================================
    # EXTRACT DECLARATION
    # =====================================================
    def process_decl(
        self,
        decl,
        module_data
    ):

        decl_type = decl.__class__.__name__

        signal_data = {

            "name": decl.name,

            "width": self.get_width(decl)
        }

        # INPUT
        if decl_type == "Input":

            self.safe_add(
                module_data["inputs"],
                signal_data
            )

            self.safe_add(
                module_data["ports"],
                decl.name
            )

        # OUTPUT
        elif decl_type == "Output":

            self.safe_add(
                module_data["outputs"],
                signal_data
            )

            self.safe_add(
                module_data["ports"],
                decl.name
            )

        # WIRE
        elif decl_type == "Wire":

            self.safe_add(
                module_data["wires"],
                signal_data
            )

        # REG
        elif decl_type == "Reg":

            self.safe_add(
                module_data["regs"],
                signal_data
            )

    # =====================================================
    # EXTRACT MODULES
    # =====================================================
    def extract_modules(self):

        if self.ast is None:

            self.parse_file()

        description = self.ast.description

        for definition in description.definitions:

            if definition.__class__.__name__ != "ModuleDef":
                continue

            module_data = {

                "module_name": definition.name,

                "ports": [],

                "inputs": [],

                "outputs": [],

                "wires": [],

                "regs": [],

                "instances": []
            }

            # =================================================
            # ANSI STYLE PORTS
            # =================================================
            if definition.portlist:

                for port in definition.portlist.ports:

                    # ANSI
                    if hasattr(port, "first"):

                        port_obj = port.first

                        if port_obj:

                            self.process_decl(
                                port_obj,
                                module_data
                            )

                    # NON ANSI
                    elif hasattr(port, "name"):

                        self.safe_add(
                            module_data["ports"],
                            port.name
                        )

            # =================================================
            # INTERNAL DECLARATIONS
            # =================================================
            for item in definition.items:

                item_type = item.__class__.__name__

                # DECLARATIONS
                if item_type == "Decl":

                    for decl in item.list:

                        self.process_decl(
                            decl,
                            module_data
                        )

                # INSTANCES
                elif item_type == "InstanceList":

                    module_type = item.module

                    for inst in item.instances:

                        instance_data = {

                            "instance_name": inst.name,

                            "module_type": module_type,

                            "connections": []
                        }

                        # PORT CONNECTIONS
                        if hasattr(inst, "portlist"):

                            for p in inst.portlist:

                                try:

                                    connection = {

                                        "portname": p.portname,

                                        "argname": (
                                            p.argname.name
                                            if hasattr(
                                                p.argname,
                                                "name"
                                            )
                                            else str(p.argname)
                                        )
                                    }

                                    instance_data[
                                        "connections"
                                    ].append(
                                        connection
                                    )

                                except:
                                    pass

                        module_data[
                            "instances"
                        ].append(
                            instance_data
                        )

            self.modules.append(module_data)

        return self.modules


# =========================================================
# TEST
# =========================================================
if __name__ == "__main__":

    filepath = "example.v"

    parser = RTLParser(filepath)

    parser.parse_file()

    modules = parser.extract_modules()

    from pprint import pprint

    pprint(modules)