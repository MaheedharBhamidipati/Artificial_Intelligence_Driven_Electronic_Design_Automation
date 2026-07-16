from pyverilog.vparser.parser import parse
import threading

PYVERILOG_LOCK = threading.Lock()

class RTLParser:

    # =====================================================
    # INIT
    # =====================================================

    def __init__(self, filepath):

        self.filepath = filepath

        self.ast = None

        self.modules = []

    # =====================================================
    # PARSE FILE
    # =====================================================

    def parse_file(self):

        with PYVERILOG_LOCK:

            try:

                ast, _ = parse([self.filepath])

                self.ast = ast

                return ast

            except Exception as e:

                raise RuntimeError(
                    f"PyVerilog parse failed: {e}"
                )

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

            except Exception:

                return 1

        return 1

    # =====================================================
    # PROCESS DECLARATION
    # =====================================================

    def process_decl(
        self,
        decl,
        module_data=None
    ):

        try:

            decl_type = decl.__class__.__name__

            # =============================================
            # INPUT
            # =============================================

            if decl_type == "Input":

                data = {

                    "name": decl.name,

                    "width": self.get_width(decl)
                }

                if module_data is not None:

                    module_data["inputs"].append(data)

                    self.safe_add(
                        module_data["ports"],
                        decl.name
                    )

                return data

            # =============================================
            # OUTPUT
            # =============================================

            elif decl_type == "Output":

                data = {

                    "name": decl.name,

                    "width": self.get_width(decl)
                }

                if module_data is not None:

                    module_data["outputs"].append(data)

                    self.safe_add(
                        module_data["ports"],
                        decl.name
                    )

                return data

            # =============================================
            # WIRE
            # =============================================

            elif decl_type == "Wire":

                data = {

                    "name": decl.name,

                    "width": self.get_width(decl)
                }

                if module_data is not None:

                    module_data["wires"].append(data)

                return data

            # =============================================
            # REG
            # =============================================

            elif decl_type == "Reg":

                data = {

                    "name": decl.name,

                    "width": self.get_width(decl)
                }

                if module_data is not None:

                    module_data["regs"].append(data)

                return data

            # =============================================
            # ASSIGN
            # =============================================

            elif decl_type == "Assign":

                return {

                    "type": "assign"
                }

            # =============================================
            # ALWAYS
            # =============================================

            elif decl_type == "Always":

                return {

                    "type": "always"
                }

            # =============================================
            # INSTANCE LIST
            # =============================================

            elif decl_type == "InstanceList":

                return {

                    "type": "instance"
                }

            # =============================================
            # UNKNOWN
            # =============================================

            return None

        except Exception as e:

            print(
                "process_decl error:",
                str(e)
            )

            return None

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
            # ANSI / NON ANSI PORTS
            # =================================================

            if definition.portlist:

                for port in definition.portlist.ports:

                    # ANSI STYLE
                    if hasattr(port, "first"):

                        port_obj = port.first

                        if port_obj:

                            self.process_decl(
                                port_obj,
                                module_data
                            )

                    # NON ANSI STYLE
                    elif hasattr(port, "name"):

                        self.safe_add(
                            module_data["ports"],
                            port.name
                        )

            # =================================================
            # INTERNAL ITEMS
            # =================================================

            for item in definition.items:

                item_type = item.__class__.__name__

                # =============================================
                # DECLARATIONS
                # =============================================

                if item_type == "Decl":

                    for decl in item.list:

                        self.process_decl(
                            decl,
                            module_data
                        )

                # =============================================
                # INSTANCE LISTS
                # =============================================

                elif item_type == "InstanceList":

                    module_type = item.module

                    for inst in item.instances:

                        instance_data = {

                            "instance_name": inst.name,

                            "module_type": module_type,

                            "connections": []
                        }

                        # =====================================
                        # PORT CONNECTIONS
                        # =====================================

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

                                            else str(
                                                p.argname
                                            )
                                        )
                                    }

                                    instance_data[
                                        "connections"
                                    ].append(
                                        connection
                                    )

                                except Exception:
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