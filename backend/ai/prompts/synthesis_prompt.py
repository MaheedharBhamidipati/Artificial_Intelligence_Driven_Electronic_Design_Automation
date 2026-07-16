def build_synthesis_prompt(netlist):

    return f"""
Analyze synthesized netlist.

Provide:
- gate optimization ideas
- logic depth analysis
- fanout concerns

Netlist:

{netlist}
"""