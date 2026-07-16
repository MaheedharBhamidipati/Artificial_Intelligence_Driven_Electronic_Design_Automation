def elaborate_hierarchy(modules, top_module):
    """
    Recursively elaborate module hierarchy.
    """
    elaborated = {
        "top": top_module,
        "instances": []
    }

    def recurse(module_name, parent_path=""):
        if module_name not in modules:
            return []

        elaborated_instances = []

        for inst in modules[module_name]["instances"]:
            full_name = f"{parent_path}/{inst['instance_name']}" if parent_path else inst["instance_name"]

            node = {
                "path": full_name,
                "type": inst["module_type"],
                "connections": inst["connections"]
            }

            elaborated_instances.append(node)

            child_instances = recurse(inst["module_type"], full_name)
            elaborated_instances.extend(child_instances)

        return elaborated_instances

    elaborated["instances"] = recurse(top_module)

    return elaborated
