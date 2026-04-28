#!/usr/bin/env python3
import logging
import os
import subprocess
import sys
from datetime import datetime

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


def step(n: int, total: int, name: str) -> None:
    """Print and log a numbered pipeline step header."""
    print()
    print("=" * 45)
    print(f"  {n}/{total}  {name}")
    print("=" * 45)
    logging.info("STEP %d/%d: %s", n, total, name)


def run(script: str) -> None:
    """Run one pipeline script and stop the pipeline if it fails."""
    result = subprocess.run([sys.executable, script], check=False)
    if result.returncode != 0:
        logging.error("FATAL: %s exited with code %d", script, result.returncode)
        print(f"Pipeline failed at {script}. Check logs/pipeline.log for details.", file=sys.stderr)
        sys.exit(result.returncode)


def main() -> None:
    """Run the full collection, processing, and analysis pipeline."""
    logging.info("Pipeline started")

    step(1, 4, "Collecting TMDB data")
    run("api_collector.py")

    step(2, 4, "Scraping IMDb data")
    run("web_scraper.py")

    step(3, 4, "Processing data")
    run("data_processor.py")

    step(4, 4, "Analyzing data")
    run("analyze_data.py")

    print()
    print("=" * 45)
    print("  Pipeline complete")
    print("=" * 45)
    logging.info("Pipeline finished successfully")

    print()
    print("Outputs:")
    print("  data/processed/movies.csv")
    print("  data/analysis/rating_analysis.png")
    print("  data/analysis/genre_analysis.png")
    print("  data/analysis/financial_analysis.png")
    print("  data/analysis/temporal_analysis.png")
    print("  REPORT.md")
    print("  logs/pipeline.log")


if __name__ == "__main__":
    main()
