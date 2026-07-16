def add_metadata(svg_element, gate):

    svg_element.update({
        "data-gate-id": gate["gate_id"],
        "data-gate-type": gate["gate_type"],
        "data-output": gate["output"],
        "data-inputs": ",".join(gate["inputs"])
    })

    return svg_element
