# ============================================================
# ROUTING UTILS
# ============================================================

def get_block_map(blocks):

    block_map = {}

    for block in blocks:

        block_map[

            block["name"]

        ] = block

    return block_map