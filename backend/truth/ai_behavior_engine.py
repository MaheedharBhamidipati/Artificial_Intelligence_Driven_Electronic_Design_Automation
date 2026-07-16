import os
import json

from dotenv import load_dotenv
from groq import Groq

# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

# =========================================================
# API KEY
# =========================================================

GROQ_API_KEY = os.getenv(
    "GROQ_BEHAVIOR_API_KEY"
)

if not GROQ_API_KEY:

    raise ValueError(
        "GROQ_BEHAVIOR_API_KEY not found in .env"
    )

# =========================================================
# GLOBAL CLIENT
# =========================================================

client = Groq(
    api_key=GROQ_API_KEY
)

# =========================================================
# RTL ANALYZER
# =========================================================

def analyze_rtl_behavior(code):

    prompt = f"""
You are a senior RTL engineer.

Analyze the Verilog RTL below.

Return ONLY valid JSON.

Required JSON format:

{{
    "logic_type":"combinational|sequential|mixed",
    "is_fsm":true,
    "states":["IDLE","START"],
    "inputs":["a","b"],
    "outputs":["y"],
    "summary":"short summary"
}}

RTL:

{code}
"""

    try:

        response = client.chat.completions.create(

            model="meta-llama/llama-4-scout-17b-16e-instruct",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0

        )

        content = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        content = (
            content
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        return json.loads(content)

    except Exception as e:

        print(
            "AI Behavior Engine Error:",
            str(e)
        )

        return {

            "logic_type":
                "unknown",

            "is_fsm":
                False,

            "states":
                [],

            "inputs":
                [],

            "outputs":
                [],

            "summary":
                f"AI parse failed: {str(e)}"
        }