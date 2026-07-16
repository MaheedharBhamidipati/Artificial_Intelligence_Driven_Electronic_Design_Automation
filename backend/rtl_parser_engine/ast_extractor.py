from pyverilog.vparser.ast import ModuleDef, InstanceList, Decl, Input, Output, Wire


def extract_modules(ast):
    """
    Extract module definitions, ports, wires, and instances.
    """
    modules = {}

    for desc in ast.description.definitions:
        if isinstance(desc, ModuleDef):
            module_name = desc.name

            modules[module_name] = {
                "ports": {
                    "inputs": [],
                    "outputs": []
                },
                "wires": [],
                "instances": []
            }

            for item in desc.items:

                if isinstance(item, Decl):
                    for decl in item.list:
                        if isinstance(decl, Input):
                            modules[module_name]["ports"]["inputs"].append(decl.name)
                        elif isinstance(decl, Output):
                            modules[module_name]["ports"]["outputs"].append(decl.name)
                        elif isinstance(decl, Wire):
                            modules[module_name]["wires"].append(decl.name)

                elif isinstance(item, InstanceList):
                    for inst in item.instances:
                        instance_data = {
                            "instance_name": inst.name,
                            "module_type": item.module,
                            "connections": {}
                        }

                        for port in inst.portlist:
                            instance_data["connections"][port.portname] = str(port.argname)

                        modules[module_name]["instances"].append(instance_data)

    return modules
