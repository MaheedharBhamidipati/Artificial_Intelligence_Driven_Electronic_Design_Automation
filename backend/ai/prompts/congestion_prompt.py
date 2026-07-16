def build_congestion_prompt(data):

    return f"""
Analyze routing congestion.

Provide:
- hotspot locations
- congestion causes
- optimization suggestions

Data:

{data}
"""