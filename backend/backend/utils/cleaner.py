import os
import shutil
import time
import subprocess
import logging

# =========================================================
# 📁 PATH CONFIG
# =========================================================
RUNS_PATH = "D:/AI_EDA_TOOL/runs/"
LOG_PATH = "D:/AI_EDA_TOOL/logs"

os.makedirs(LOG_PATH, exist_ok=True)

# =========================================================
# 🧠 LOGGING SETUP
# =========================================================
logger = logging.getLogger("cleaner")

logger.setLevel(logging.ERROR)  # 🔥 Default: only errors

file_handler = logging.FileHandler(os.path.join(LOG_PATH, "cleaner.log"))
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
))

logger.addHandler(file_handler)

# =========================================================
# ⚙️ PROCESS KILLER
# =========================================================
def kill_simulation_processes():
    """
    Kill simulation tools that may lock files
    """
    processes = ["vvp.exe", "iverilog.exe"]

    for proc in processes:
        try:
            subprocess.call(
                f"taskkill /f /im {proc}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info(f"Killed process: {proc}")
        except Exception as e:
            logger.warning(f"Failed to kill {proc}: {e}")

# =========================================================
# 🧹 SAFE DELETE
# =========================================================
def safe_delete(path, retries=3, delay=1):
    """
    Safely delete file or folder with retries
    """
    for attempt in range(retries):
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
                logger.info(f"Deleted file: {path}")
                return True

            elif os.path.isdir(path):
                shutil.rmtree(path)
                logger.info(f"Deleted folder: {path}")
                return True

        except PermissionError:
            logger.warning(f"File locked (attempt {attempt+1}): {path}")
            time.sleep(delay)

        except Exception as e:
            logger.error(f"Error deleting {path}: {e}")
            return False

    logger.error(f"Failed after retries: {path}")
    return False

# =========================================================
# 🧠 MAIN CLEAN FUNCTION
# =========================================================
def clear_runs(debug=False):
    """
    Clean runs directory safely

    Args:
        debug (bool): If True, enables verbose logging
    """

    # 🔥 Enable debug logs dynamically
    if debug:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.ERROR)

    if not os.path.exists(RUNS_PATH):
        logger.warning("Runs folder does not exist")
        return

    # 🔥 Step 1: Kill simulation processes
    kill_simulation_processes()

    # 🔥 Step 2: Delete files
    for filename in os.listdir(RUNS_PATH):
        file_path = os.path.join(RUNS_PATH, filename)

        success = safe_delete(file_path)

        if success:
            logger.info(f"Deleted: {file_path}")
        else:
            logger.warning(f"Skipped: {file_path}")
