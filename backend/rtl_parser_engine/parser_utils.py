import json


def save_json(data, filename="output.json"):

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

    print(f"\nSaved JSON -> {filename}")


def load_verilog(filepath):

    with open(filepath, "r") as f:
        return f.read()
