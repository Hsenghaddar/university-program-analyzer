import subprocess
import sys


def run_step(script_name):
    result = subprocess.run([sys.executable, script_name])
    if result.returncode != 0:
        raise SystemExit(f"Failed while running {script_name}")


def main():
    run_step("scraper.py")
    run_step("cleaner.py")
    run_step("webometrics_ranking.py")


if __name__ == "__main__":
    main()