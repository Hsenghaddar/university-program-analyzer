import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def run_step(script_name):
    result = subprocess.run([sys.executable, str(BASE_DIR / script_name)])
    if result.returncode != 0:
        raise SystemExit(f"Failed while running {script_name}")


def main():
    run_step("scrapper.py")
    run_step("cleaner.py")
    run_step("webometrics_ranking.py")


if __name__ == "__main__":
    main()