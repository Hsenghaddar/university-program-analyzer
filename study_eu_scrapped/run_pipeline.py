import subprocess
import sys


def run_step(script_name):
    result = subprocess.run([sys.executable, script_name])
    if result.returncode != 0:
        raise SystemExit(f"Failed while running {script_name}")


def main():
    run_step("study_eu_scrapped/study_eu_scraper.py")
    run_step("study_eu_scrapped/clean_study_eu.py")
    run_step("study_eu_scrapped/add_webometrics_ranking.py")


if __name__ == "__main__":
    main()