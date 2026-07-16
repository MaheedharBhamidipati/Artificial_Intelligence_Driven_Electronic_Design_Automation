# =========================================================
# AIDEA RTL SCHEMATIC GENERATOR
# PRODUCTION VERSION
# Yosys -> Graphviz pipeline, job-isolated & cross-platform
# =========================================================

import os
import re
import sys
import uuid
import logging
import platform
import subprocess
import textwrap
import shutil
import time
from pathlib import Path

from backend.schematic.svg_interactive import inject_interactivity

# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger("aidea.schematic_generator")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# =========================================================
# PATHS (env-overridable, cross-platform)
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent

UPLOAD_DIR = Path(os.environ.get("AIDEA_UPLOAD_DIR", PROJECT_ROOT / "backend" / "uploads"))
SCHEMATIC_DIR = Path(os.environ.get("AIDEA_SCHEMATIC_DIR", PROJECT_ROOT / "static" / "schematics"))
OSS_CAD_DIR = Path(os.environ.get("AIDEA_OSS_CAD_DIR", PROJECT_ROOT / "oss-cad-suite"))

_IS_WINDOWS = platform.system() == "Windows"

# Allow full override via env var; otherwise resolve platform-correct binary name.
YOSYS_EXE = os.environ.get(
    "AIDEA_YOSYS_PATH",
    str(OSS_CAD_DIR / "bin" / ("yosys.exe" if _IS_WINDOWS else "yosys")),
)
DOT_EXE = os.environ.get("AIDEA_DOT_PATH", "dot")

# Job artifacts get pruned after this many seconds (default 1 hour).
JOB_TTL_SECONDS = int(os.environ.get("AIDEA_SCHEMATIC_TTL", "3600"))

# Hard caps to prevent abuse / runaway subprocess time.
MAX_VERILOG_BYTES = int(os.environ.get("AIDEA_MAX_VERILOG_BYTES", str(2 * 1024 * 1024)))  # 2 MB
YOSYS_TIMEOUT_SECONDS = int(os.environ.get("AIDEA_YOSYS_TIMEOUT", "60"))
GRAPHVIZ_TIMEOUT_SECONDS = int(os.environ.get("AIDEA_GRAPHVIZ_TIMEOUT", "30"))


def _ensure_dirs():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    SCHEMATIC_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# VERIFY TOOLS
# =========================================================

def verify_tools():
    if not Path(YOSYS_EXE).exists():
        return False, f"Yosys not found at: {YOSYS_EXE} (set AIDEA_YOSYS_PATH to override)"

    try:
        result = subprocess.run(
            [DOT_EXE, "-V"], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return False, "Graphviz 'dot' command failed to run."
    except FileNotFoundError:
        return False, "Graphviz not installed or not on PATH (set AIDEA_DOT_PATH to override)."
    except subprocess.TimeoutExpired:
        return False, "Graphviz version check timed out."
    except Exception as e:
        return False, f"Graphviz check failed: {e}"

    return True, ""


# =========================================================
# VALIDATION / SANITIZATION
# =========================================================

def sanitize_name(name):
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)[:64] or "top"


def validate_verilog(verilog_code):
    if not verilog_code or not verilog_code.strip():
        raise ValueError("Verilog source is empty.")

    encoded_size = len(verilog_code.encode("utf-8"))
    if encoded_size > MAX_VERILOG_BYTES:
        raise ValueError(
            f"Verilog source too large ({encoded_size} bytes, max {MAX_VERILOG_BYTES})."
        )

    if "module" not in verilog_code:
        raise ValueError("No 'module' keyword found — not valid Verilog source.")


# =========================================================
# EXTRACT TOP MODULE
# =========================================================

def extract_top_module(verilog_code):
    modules = re.findall(r"\bmodule\s+([a-zA-Z_][a-zA-Z0-9_]*)", verilog_code)
    if not modules:
        return "top"

    instantiated = re.findall(
        r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(", verilog_code
    )
    keywords = {"if", "for", "while", "case", "assign", "always", "module"}
    instantiated = {x for x in instantiated if x not in keywords}

    possible_tops = [m for m in modules if m not in instantiated]
    return possible_tops[-1] if possible_tops else modules[-1]


# =========================================================
# SVG OPTIMIZATION
# =========================================================

def optimize_svg(svg_file: Path):
    if not svg_file.exists():
        return

    svg = svg_file.read_text(encoding="utf-8", errors="ignore")

    svg = re.sub(r'width="[^"]+"', "", svg)
    svg = re.sub(r'height="[^"]+"', "", svg)

    svg = re.sub(r'stroke=""', 'stroke="#475569"', svg)
    svg = re.sub(r"stroke=([ >])", r'stroke="#475569"\1', svg)
    svg = re.sub(r'fill=""', 'fill="none"', svg)
    svg = re.sub(r"fill=([ >])", r'fill="none"\1', svg)
    svg = re.sub(r'stroke-width=""', 'stroke-width="2"', svg)
    svg = re.sub(r'font-size=""', 'font-size="16"', svg)
    svg = re.sub(r'font-family=""', 'font-family="Arial"', svg)

    svg = svg.replace("\ufffe", "")

    style = """
<style>
svg{ background:white; }
text{
    font-family: Arial, Helvetica, sans-serif;
    font-size:18px;
    font-weight:bold;
    fill:#111827;
}
polygon, path, rect, circle, ellipse, line{ stroke-width:2; }
.node rect{ fill:#f8fafc; stroke:#334155; }
.edge path{ stroke:#475569; }
</style>
"""
    if "</svg>" in svg:
        svg = svg.replace("</svg>", f"{style}</svg>")

    # Add click/hover metadata hooks so the frontend can highlight gates
    # consistently, whether the schematic came from this Graphviz path
    # or the custom LayoutEngine/SVGRenderer path.
    svg = inject_interactivity(svg)

    svg_file.write_text(svg, encoding="utf-8", errors="ignore")


# =========================================================
# YOSYS SCRIPT
# =========================================================

def create_yosys_script(verilog_file: Path, top_module: str, output_prefix: Path):
    prefix = str(output_prefix).replace("\\", "/")
    verilog_path = str(verilog_file).replace("\\", "/")

    script = f"""
read_verilog "{verilog_path}"

hierarchy -auto-top
hierarchy -check -top {top_module}

proc
opt

memory
opt

fsm
opt

clean

show \\
-stretch \\
-width \\
-format dot \\
-prefix {prefix} \\
-colors 8 \\
-notitle
"""
    return textwrap.dedent(script)


# =========================================================
# RUN YOSYS / GRAPHVIZ (with timeouts)
# =========================================================

def run_yosys(yosys_script_file: Path):
    command = [YOSYS_EXE, "-s", str(yosys_script_file)]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=YOSYS_TIMEOUT_SECONDS
        )
    except subprocess.TimeoutExpired:
        logger.error("Yosys timed out after %ss", YOSYS_TIMEOUT_SECONDS)
        raise TimeoutError(f"Yosys synthesis timed out after {YOSYS_TIMEOUT_SECONDS}s.")

    logger.debug("Yosys stdout: %s", result.stdout)
    if result.returncode != 0:
        logger.warning("Yosys stderr: %s", result.stderr)

    return result


def run_graphviz(dot_file: Path, svg_file: Path, png_file: Path):
    base_args = [DOT_EXE, "-Gsplines=polyline", "-Grankdir=LR"]

    try:
        svg_result = subprocess.run(
            base_args + [
                "-Gnodesep=0.7", "-Granksep=1.5",
                "-Gconcentrate=true", "-Goverlap=false",
                "-Gpack=true", "-Gpackmode=cluster",
                "-Tsvg", str(dot_file), "-o", str(svg_file),
            ],
            capture_output=True, text=True, timeout=GRAPHVIZ_TIMEOUT_SECONDS,
        )
        png_result = subprocess.run(
            base_args + ["-Tpng", str(dot_file), "-o", str(png_file)],
            capture_output=True, text=True, timeout=GRAPHVIZ_TIMEOUT_SECONDS,
        )
        if png_result.returncode != 0:
            # PNG is a secondary/preview artifact — don't fail the whole
            # job over it, but don't silently swallow the error either.
            logger.warning("PNG render failed (SVG still used as primary output): %s", png_result.stderr)
    except subprocess.TimeoutExpired:
        logger.error("Graphviz timed out after %ss", GRAPHVIZ_TIMEOUT_SECONDS)
        raise TimeoutError(f"Graphviz rendering timed out after {GRAPHVIZ_TIMEOUT_SECONDS}s.")

    return svg_result


# =========================================================
# CLEANUP OLD JOBS (call periodically, e.g. via APScheduler/cron)
# =========================================================

def cleanup_expired_jobs():
    """Remove job directories older than JOB_TTL_SECONDS."""
    now = time.time()
    for base in (UPLOAD_DIR, SCHEMATIC_DIR):
        if not base.exists():
            continue
        for job_dir in base.iterdir():
            if not job_dir.is_dir():
                continue
            try:
                age = now - job_dir.stat().st_mtime
                if age > JOB_TTL_SECONDS:
                    shutil.rmtree(job_dir, ignore_errors=True)
                    logger.info("Cleaned up expired job dir: %s", job_dir)
            except FileNotFoundError:
                continue


# =========================================================
# MAIN ENTRY POINT
# =========================================================

def generate_schematic(verilog_code: str):
    """
    Generate an SVG/PNG schematic from Verilog source.
    Each call is isolated in its own job directory (uuid-based),
    so concurrent requests never collide on filenames.
    """
    job_id = uuid.uuid4().hex[:12]

    try:
        _ensure_dirs()
        validate_verilog(verilog_code)

        tools_ok, tool_error = verify_tools()
        if not tools_ok:
            return {"success": False, "error": tool_error}

        top_module = sanitize_name(extract_top_module(verilog_code))

        job_upload_dir = UPLOAD_DIR / job_id
        job_schematic_dir = SCHEMATIC_DIR / job_id
        job_upload_dir.mkdir(parents=True, exist_ok=True)
        job_schematic_dir.mkdir(parents=True, exist_ok=True)

        verilog_file = job_upload_dir / f"{top_module}.v"
        yosys_script_file = job_upload_dir / f"{top_module}.ys"
        dot_file = job_schematic_dir / f"{top_module}.dot"
        svg_file = job_schematic_dir / f"{top_module}.svg"
        png_file = job_schematic_dir / f"{top_module}.png"

        verilog_file.write_text(verilog_code, encoding="utf-8")

        yosys_script = create_yosys_script(
            verilog_file, top_module, job_schematic_dir / top_module
        )
        yosys_script_file.write_text(yosys_script, encoding="utf-8")

        logger.info("[job %s] Running Yosys for top module '%s'", job_id, top_module)
        yosys_result = run_yosys(yosys_script_file)

        if yosys_result.returncode != 0:
            return {
                "success": False,
                "error": yosys_result.stderr + "\n\n" + yosys_result.stdout,
            }

        if not dot_file.exists():
            return {"success": False, "error": "DOT file not generated."}

        logger.info("[job %s] Running Graphviz", job_id)
        graphviz_result = run_graphviz(dot_file, svg_file, png_file)

        if graphviz_result.returncode != 0:
            return {"success": False, "error": graphviz_result.stderr}

        if not svg_file.exists():
            return {"success": False, "error": "SVG generation failed."}

        optimize_svg(svg_file)

        logger.info("[job %s] Schematic generated successfully", job_id)

        return {
            "success": True,
            "job_id": job_id,
            "top_module": top_module,
            "svg_path": f"/static/schematics/{job_id}/{top_module}.svg",
            "png_path": f"/static/schematics/{job_id}/{top_module}.png",
            "dot_path": f"/static/schematics/{job_id}/{top_module}.dot",
            "message": "Schematic generated successfully.",
        }

    except (ValueError, TimeoutError) as e:
        logger.warning("[job %s] %s", job_id, e)
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.exception("[job %s] Unexpected failure", job_id)
        return {"success": False, "error": str(e)}
