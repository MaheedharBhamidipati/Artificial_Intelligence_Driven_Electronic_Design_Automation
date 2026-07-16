# ============================================================
# SIMPLE NET EXTRACTOR
# ============================================================

def extract_nets(blocks):

    nets = []

    for i in range(len(blocks) - 1):

        source = blocks[i]["name"]

        target = blocks[i + 1]["name"]

        nets.append({

            "source": source,

            "target": target
        })

    return nets