import ollama
import json
import re
from typing import Dict, Optional

# =========================================================
# CONFIGURATION (OPTIMIZED FOR LOW MEMORY SYSTEMS)
# =========================================================
MODELS = [
    "phi3",        # 🟢 Best for low RAM
    "tinyllama",   # 🟡 Backup
]

MEMORY_ERROR_KEYWORDS = [
    "requires more system memory",
    "out of memory",
]

TIMEOUT_ERROR_KEYWORDS = [
    "timeout",
    "timed out",
]

# =========================================================
# CLEANING UTILITIES
# =========================================================
def remove_ansi(text: str) -> str:
    """Remove terminal ANSI escape characters"""
    return re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', text)


def strip_markdown(text: str) -> str:
    """Remove markdown code fences"""
    text = re.sub(r'```[\w]*\n?', '', text)
    return text.replace('```', '')


def clean_text(text: str) -> str:
    """Full cleanup pipeline"""
    text = remove_ansi(text)
    text = strip_markdown(text)
    return text.strip()

# =========================================================
# PROMPT BUILDER
# =========================================================
def build_prompt(code: str) -> str:
    return f"""
You are an expert Verilog RTL engineer.

Your tasks:
1. Fix ALL syntax errors
2. Ensure synthesizable RTL
3. Improve readability and structure
4. Detect issues

STRICT OUTPUT FORMAT (JSON ONLY):

{{
  "fixed_code": "<correct verilog>",
  "explanation": "<numbered explanation>",
  "errors": "<list of issues>"
}}

Rules:
- No markdown
- No extra text
- Only JSON output

Verilog Code:
{code}
"""

# =========================================================
# MODEL CALL
# =========================================================
def call_model(model: str, prompt: str) -> str:
    """Call Ollama model safely"""
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": "You are a Verilog RTL expert."},
            {"role": "user", "content": prompt}
        ]
    )
    return response["message"]["content"]

# =========================================================
# RESPONSE PARSER
# =========================================================
def parse_response(raw: str) -> Dict:

    raw = clean_text(raw)

    try:

        parsed = json.loads(raw)

        explanation = parsed.get(
            "explanation",
            ""
        )

        errors = parsed.get(
            "errors",
            []
        )

        # =============================================
        # FORCE CLEAN NUMBERED FORMAT
        # =============================================
        if isinstance(explanation, list):

            explanation = "\n".join(
                [
                    f"{i+1}. {item}"
                    for i, item in enumerate(explanation)
                ]
            )

        if isinstance(errors, list):

            errors = "\n".join(
                [
                    f"{i+1}. {item}"
                    for i, item in enumerate(errors)
                ]
            )

        return {
            "fixed_code": parsed.get(
                "fixed_code",
                ""
            ),

            "explanation": explanation,

            "errors": errors
        }

    except Exception:

        return {
            "fixed_code": raw,
            "explanation":
                "1. AI returned non-JSON response.\n"
                "2. Showing raw output.",
            "errors":
                "1. Unable to parse structured AI response."
        }

# =========================================================
# ERROR CLASSIFIER
# =========================================================
def classify_error(error_msg: str) -> str:
    error_msg_lower = error_msg.lower()

    if any(k in error_msg_lower for k in MEMORY_ERROR_KEYWORDS):
        return "memory"
    if any(k in error_msg_lower for k in TIMEOUT_ERROR_KEYWORDS):
        return "timeout"

    return "unknown"

# =========================================================
# MAIN AI ENGINE
# =========================================================
def analyze_verilog(code: str) -> Dict:
    """
    Main entry point for AI analysis

    Returns:
    {
        fixed_code: str,
        explanation: str,
        errors: str,
        model_used: str,
        status: "success" | "failed"
    }
    """

    if not code or not code.strip():
        return {
            "fixed_code": "",
            "explanation": "",
            "errors": "Input code is empty",
            "model_used": None,
            "status": "failed"
        }

    prompt = build_prompt(code)
    last_error: Optional[str] = None

    for model in MODELS:
        try:
            raw_output = call_model(model, prompt)
            parsed = parse_response(raw_output)

            return {
                "fixed_code": parsed["fixed_code"],
                "explanation": parsed["explanation"],
                "errors": parsed["errors"],
                "model_used": model,
                "status": "success"
            }

        except Exception as e:
            last_error = str(e)
            error_type = classify_error(last_error)

            print(f"[AI ENGINE] Model {model} failed ({error_type}): {last_error}")

            # Try next model on failure
            continue

    # =====================================================
    # FINAL FAILURE
    # =====================================================
    return {
        "fixed_code": "",
        "explanation": "",
        "errors": last_error or "All models failed",
        "model_used": None,
        "status": "failed"
    }

# =========================================================
# OPTIONAL: CLI TEST MODE
# =========================================================
if __name__ == "__main__":
    print("\n🔧 Verilog AI Analyzer\n")
    print("Paste Verilog code (Ctrl+D to end):\n")

    import sys
    user_code = sys.stdin.read()

    result = analyze_verilog(user_code)

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)

    if result["status"] == "failed":
        print(f"\n❌ ERROR:\n{result['errors']}")
    else:
        print(f"\n✅ MODEL USED: {result['model_used']}")

        print("\n--- FIXED CODE ---\n")
        print(result["fixed_code"])

        print("\n--- EXPLANATION ---\n")
        print(result["explanation"])
