from openai import OpenAI

from dotenv import load_dotenv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import os
import time
import json
import re

from typing import Dict, List, Optional

# =====================================================
# LOAD ENV
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

# =====================================================
# API KEY
# =====================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env")

# =====================================================
# GROQ CLIENT
# =====================================================

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# =====================================================
# CONFIGURATION
# =====================================================

DEFAULT_MODEL = os.getenv(
    "GROQ_MODEL",
    "meta-llama/llama-4-scout-17b-16e-instruct"
)

# Character budget for the RTL portion of a single prompt (not the whole
# template). Llama-4-Scout on Groq supports a large context window, so this
# is generous but still bounded to keep latency/cost predictable.
MAX_CODE_CHARS = int(os.getenv("GROQ_MAX_CODE_CHARS", "20000"))

# Output budget per module. The full 9-section report needs real room —
# 1200 tokens was truncating responses mid-report.
MAX_OUTPUT_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "3000"))

MAX_RETRIES = int(os.getenv("GROQ_MAX_RETRIES", "3"))
RETRY_BASE_DELAY = 1.5  # seconds, exponential backoff

# How many modules to analyze concurrently. Each call is I/O bound, so
# threads (not processes) are the right tool here.
MAX_WORKERS = int(os.getenv("GROQ_MAX_WORKERS", "4"))

VALID_MODES = {"rtl_fix", "quick_review", "explain_only"}

# =====================================================
# LOGGER
# =====================================================

def log(message: str):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] [AI ENGINE] {message}")

# =====================================================
# TEXT CLEANING
# =====================================================

def remove_ansi(text: str) -> str:
    return re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', text)


def clean_text(text: str) -> str:
    """
    Light-touch cleanup only. The model's response is markdown meant to be
    rendered as-is (headings, tables, fenced code snippets). Stripping
    ``` fences here (as the old version did) destroyed the formatting of
    every corrected-RTL snippet in the report, so we no longer do that —
    we only strip terminal escape codes and surrounding whitespace.
    """
    text = remove_ansi(text)
    return text.strip()


def remove_comments(code: str) -> str:
    """
    Strip // line comments and /* */ block comments so module boundary
    detection isn't confused by a stray 'endmodule' or 'module' mentioned
    inside a comment. Does not touch string literals precisely, but that
    is a rare edge case for RTL source.
    """
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code = re.sub(r'//.*', '', code)
    return code

# =====================================================
# PROMPT TEMPLATES
# =====================================================

def _full_report_instructions() -> str:
    return """
==================================================
OUTPUT FORMAT
==================================================

Your response MUST contain the following sections.

# 1. RTL OVERVIEW

Explain:
- Overall functionality
- Design purpose
- High-level architecture
- Behavioral summary

--------------------------------------------------

# 2. MODULE INTERFACE ANALYSIS

Generate a professional Markdown table:

| Signal | Direction | Width | Description |
|--------|-----------|--------|-------------|

Include:
- Inputs
- Outputs
- Important internal signals

--------------------------------------------------

# 3. FUNCTIONAL LOGIC ANALYSIS

Explain:
- Sequential logic
- Combinational logic
- FSM behavior (if present)
- Dataflow
- Pipeline stages
- Clock behavior
- Reset behavior

Use bullet points.

--------------------------------------------------

# 4. HARDWARE IMPLEMENTATION INSIGHTS

Explain likely hardware mapping.

## FPGA Perspective
- LUT usage
- Flip-Flop usage
- DSP utilization
- BRAM utilization
- Critical path estimation

## ASIC Perspective
- Gate-level implications
- Area impact
- Power implications
- Timing implications
- Scalability

--------------------------------------------------

# 5. TIMING ANALYSIS

Explain:
- Critical timing paths
- Setup timing risks
- Hold timing risks
- Clock domain issues
- Reset synchronization issues
- Fanout concerns
- Pipeline recommendations

--------------------------------------------------

# 6. RTL QUALITY CHECK

Report using this table:

| Check | Status | Details |
|-------|--------|---------|

Checks include:
- Synthesizable RTL
- Latch inference
- Combinational loops
- Width mismatch
- Blocking/non-blocking misuse
- Multiple drivers
- CDC issues
- Reset quality
- FSM safety
- Timing safety

Use: PASS / WARNING / ERROR

--------------------------------------------------

# 7. ERROR DETECTION & FIXES

If errors exist, for EACH one provide, in this exact order:
- **Issue:** exact problem
- **Root Cause:** why it happens
- **Impact:** engineering consequence
- **Fix:** a fenced ```verilog code block containing ONLY the corrected
  section (never the full module)

If no issues exist, state exactly:
"No major RTL design issues detected."

--------------------------------------------------

# 8. OPTIMIZATION SUGGESTIONS

Suggest improvements for performance, area, power, timing, FPGA
optimization, ASIC optimization, readability, and scalability.

--------------------------------------------------

# 9. FINAL ENGINEERING SUMMARY

Provide a summary table:

| Category | Rating |
|----------|--------|

Rows: Overall RTL Quality, FPGA Readiness, ASIC Readiness, Timing
Reliability, Synthesizability, Production Readiness.
Ratings: Excellent / Good / Moderate / Poor
"""


def _quick_review_instructions() -> str:
    return """
==================================================
OUTPUT FORMAT (QUICK REVIEW)
==================================================

# OVERVIEW
2-4 sentences on what this module does.

# ISSUES FOUND
Bullet list. For each real issue: what it is, why it's wrong, and a short
fenced ```verilog fix for just that section. If none, state exactly:
"No major RTL design issues detected."

# RATING
| Category | Rating |
|----------|--------|
Rows: Synthesizability, Timing Reliability, Production Readiness.
Ratings: Excellent / Good / Moderate / Poor
"""


def _explain_only_instructions() -> str:
    return """
==================================================
OUTPUT FORMAT (EXPLAIN ONLY — NO FIXES)
==================================================

# 1. RTL OVERVIEW
Design purpose, high-level architecture, behavioral summary.

# 2. MODULE INTERFACE ANALYSIS
| Signal | Direction | Width | Description |
|--------|-----------|--------|-------------|

# 3. FUNCTIONAL LOGIC ANALYSIS
Sequential logic, combinational logic, FSM behavior, dataflow, clock and
reset behavior, in bullet points.

# 4. HARDWARE IMPLEMENTATION INSIGHTS
Likely FPGA and ASIC mapping at a high level.

Do NOT flag or fix errors in this mode — pure explanation only.
"""


_MODE_INSTRUCTIONS = {
    "rtl_fix": _full_report_instructions,
    "quick_review": _quick_review_instructions,
    "explain_only": _explain_only_instructions,
}


def build_prompt(code: str, mode: str = "rtl_fix") -> str:
    mode = mode if mode in VALID_MODES else "rtl_fix"

    instructions = _MODE_INSTRUCTIONS[mode]()

    return f"""
You are AIDEA AI Engine — an elite semiconductor AI system specialized in
RTL Design, Verilog, SystemVerilog, FPGA Design, ASIC Design, Digital
Electronics, CMOS Design, Static Timing Analysis, Physical Design,
Synthesis, DFT, CDC Analysis, and Advanced VLSI Systems.

==================================================
PRIMARY OBJECTIVE
==================================================

Analyze the RTL code below with maximum engineering accuracy and
educational depth. Be highly structured, deeply technical, professional,
and industry-grade. Format cleanly in Markdown.

==================================================
CRITICAL RESPONSE RULES
==================================================

- Do NOT repeat the full RTL code in your explanation.
- Do NOT dump unnecessary raw code.
- Do NOT give vague, generic explanations — reference actual signal
  names, widths, and constructs from the code below.
- Detect (where applicable): logical/design mistakes, synthesis issues,
  timing problems, FPGA/ASIC implementation risks, latch inference,
  combinational loops, clock/reset problems, race conditions,
  blocking/non-blocking misuse, width mismatches, unused signals, and
  optimization opportunities.
- If the RTL is already good, explicitly say so rather than inventing
  problems.

{instructions}

==================================================
RTL CODE TO ANALYZE
==================================================

```verilog
{code}
```
"""

# =====================================================
# MAIN AI CALL (with retry/backoff)
# =====================================================

def generate_ai_explanation(prompt: str) -> str:
    if len(prompt) > MAX_CODE_CHARS + 6000:
        # Safety net in case an oversized module slips through upstream
        # truncation. Trims the prompt tail-first so instructions at the
        # top of the template are preserved.
        prompt = prompt[: MAX_CODE_CHARS + 6000]

    last_error: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert ASIC, FPGA, RTL, synthesis, "
                            "timing analysis, and semiconductor engineer. "
                            "You always answer in precise, well-structured "
                            "Markdown and never fabricate issues that "
                            "aren't actually present in the code."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=MAX_OUTPUT_TOKENS,
            )
            return response.choices[0].message.content

        except Exception as e:
            last_error = e
            err_str = str(e)

            if "413" in err_str:
                return (
                    "AI Explanation Error: Input RTL too large. "
                    "Try analyzing module-wise."
                )

            # Retry on rate limiting / transient server errors only.
            retryable = any(
                code in err_str for code in ("429", "500", "502", "503", "504")
            )

            if retryable and attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                log(f"Retryable error ({err_str}), retrying in {delay:.1f}s "
                    f"[attempt {attempt}/{MAX_RETRIES}]")
                time.sleep(delay)
                continue

            break

    return f"AI Explanation Error: {str(last_error)}"

# =====================================================
# RESPONSE PARSER
# =====================================================

_CODE_BLOCK_RE = re.compile(r"```(?:verilog|systemverilog|v)?\s*\n(.*?)```", re.DOTALL)


def _extract_section(raw: str, header_num: int) -> Optional[str]:
    """Pull the text of a numbered '# N. TITLE' section out of the report."""
    pattern = rf"#\s*{header_num}\.[^\n]*\n(.*?)(?=\n#\s*\d+\.|\Z)"
    match = re.search(pattern, raw, re.DOTALL)
    return match.group(1).strip() if match else None


def _extract_fixed_code(raw: str) -> str:
    """
    Collect every fenced code block that appears inside the
    ERROR DETECTION & FIXES section (full report) or anywhere in the
    response (quick review), since that's the only place corrected RTL
    snippets should appear.
    """
    section = _extract_section(raw, 7)
    search_text = section if section else raw

    blocks = _CODE_BLOCK_RE.findall(search_text)
    return "\n\n".join(b.strip() for b in blocks).strip()


def _extract_errors(raw: str) -> str:
    section = _extract_section(raw, 7)
    if not section:
        return ""

    if re.search(r"no major rtl design issues detected", section, re.IGNORECASE):
        return ""

    # Strip fenced code blocks out of the errors summary so it stays
    # readable as a plain-text/markdown issue list without duplicating
    # the fixed_code payload.
    return _CODE_BLOCK_RE.sub("", section).strip()


def parse_response(raw: str) -> Dict:
    raw = clean_text(raw)

    fixed_code = _extract_fixed_code(raw)
    errors = _extract_errors(raw)

    return {
        "fixed_code": fixed_code,
        "explanation": "RTL analysis completed successfully",
        "errors": errors,
        "ai_explanation": raw,
    }

# =====================================================
# MODULE EXTRACTION / CHUNKING
# =====================================================

def chunk_text(text: str, chunk_size: int = 2500) -> List[str]:
    """
    Fallback chunking for files where no `module ... endmodule` block is
    found (e.g. package files, headers, snippets). Splits on line
    boundaries rather than raw character offsets so a chunk never cuts a
    statement in half.
    """
    lines = text.splitlines(keepends=True)
    chunks, current = [], ""

    for line in lines:
        if len(current) + len(line) > chunk_size and current:
            chunks.append(current)
            current = ""
        current += line

    if current:
        chunks.append(current)

    return chunks or [text]


def extract_modules(verilog_code: str) -> List[str]:
    pattern = r'\bmodule\s+.*?\bendmodule\b'
    return re.findall(pattern, verilog_code, re.DOTALL)

# =====================================================
# MAIN ANALYZER
# =====================================================

def _analyze_single_module(idx: int, module_code: str, mode: str) -> Dict:
    module_name_match = re.search(r'module\s+(\w+)', module_code)
    module_name = module_name_match.group(1) if module_name_match else f"block_{idx + 1}"

    log(f"Analyzing module: {module_name}")

    truncated = len(module_code) > MAX_CODE_CHARS
    code_for_prompt = module_code[:MAX_CODE_CHARS] if truncated else module_code

    prompt = build_prompt(code_for_prompt, mode)
    raw_output = generate_ai_explanation(prompt)
    parsed = parse_response(raw_output)

    return {
        "module_name": module_name,
        "truncated": truncated,
        **parsed,
    }


def analyze_verilog(
    code: str,
    mode: str = "rtl_fix",
    stream: bool = False
) -> Dict:

    if not code or not code.strip():
        return {
            "status": "failed",
            "fixed_code": "",
            "explanation": "",
            "errors": "Input RTL code is empty",
            "ai_explanation": "",
            "model_used": None,
            "modules": [],
        }

    if mode not in VALID_MODES:
        log(f"Unknown mode '{mode}', defaulting to 'rtl_fix'")
        mode = "rtl_fix"

    try:
        log(f"Using model: {DEFAULT_MODEL}")

        cleaned_code = remove_comments(code)
        modules = extract_modules(cleaned_code)

        if len(modules) == 0:
            log("No 'module ... endmodule' block found — chunking file instead")
            modules = chunk_text(cleaned_code, 2500)

        module_results: List[Optional[Dict]] = [None] * len(modules)

        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(modules))) as pool:
            futures = {
                pool.submit(_analyze_single_module, idx, module, mode): idx
                for idx, module in enumerate(modules)
            }
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    module_results[idx] = future.result()
                except Exception as e:
                    log(f"Module {idx} failed: {e}")
                    module_results[idx] = {
                        "module_name": f"block_{idx + 1}",
                        "truncated": False,
                        "fixed_code": "",
                        "explanation": "Analysis failed for this module",
                        "errors": str(e),
                        "ai_explanation": f"AI Explanation Error: {e}",
                    }

        # ---------------------------------------------
        # AGGREGATE — every module's explanation is now
        # actually included, not just the last one.
        # ---------------------------------------------

        combined_sections = []
        combined_fixed_code = []
        combined_errors = []

        for result in module_results:
            header = f"## Module: `{result['module_name']}`"
            if result.get("truncated"):
                header += " (input truncated to fit prompt size limit)"
            combined_sections.append(f"{header}\n\n{result['ai_explanation']}")

            if result.get("fixed_code"):
                combined_fixed_code.append(
                    f"// ---- {result['module_name']} ----\n{result['fixed_code']}"
                )
            if result.get("errors"):
                combined_errors.append(
                    f"### {result['module_name']}\n{result['errors']}"
                )

        ai_explanation = "\n\n---\n\n".join(combined_sections)
        fixed_code = "\n\n".join(combined_fixed_code)
        errors = "\n\n".join(combined_errors)

        log(f"AI analysis completed for {len(modules)} module(s)")

        return {
            "status": "success",
            "fixed_code": fixed_code,
            "explanation": (
                f"RTL analysis completed successfully for {len(modules)} "
                f"module(s)"
            ),
            "errors": errors,
            "ai_explanation": ai_explanation,
            "model_used": DEFAULT_MODEL,
            "modules": module_results,
        }

    except Exception as e:
        log(f"AI Engine Error: {str(e)}")
        return {
            "status": "failed",
            "fixed_code": code,
            "explanation": "AI analysis failed",
            "errors": str(e),
            "ai_explanation": str(e),
            "model_used": DEFAULT_MODEL,
            "modules": [],
        }

# =====================================================
# CLI TEST MODE
# =====================================================

if __name__ == "__main__":

    print("\nAIDEA Groq AI Analyzer\n")

    import sys

    args = sys.argv[1:]
    cli_mode = "rtl_fix"

    if args and args[0] in VALID_MODES:
        cli_mode = args[0]
        args = args[1:]

    if args:
        # Optional: python ai_engine.py [mode] path/to/file.v
        with open(args[0], "r") as f:
            user_code = f.read()
    else:
        user_code = sys.stdin.read()

    result = analyze_verilog(user_code, mode=cli_mode)

    print("\n" + "=" * 70)
    print("AIDEA RESULT")
    print("=" * 70)

    print(json.dumps(result, indent=4))
