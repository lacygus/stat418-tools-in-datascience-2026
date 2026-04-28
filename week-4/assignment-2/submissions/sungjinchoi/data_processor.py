#!/usr/bin/env python3
import json
import logging
import os
from typing import Dict, List, Tuple

import pandas as pd

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/data_processor.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def load_raw_data() -> Tuple[List[Dict], List[Dict]]:
    """Load raw TMDB and IMDb JSON records from disk."""
    with open("data/raw/tmdb/movies.json") as f:
        tmdb = json.load(f)
    with open("data/raw/imdb/ratings.json") as f:
        imdb = json.load(f)
    logging.info("Loaded tmdb=%d imdb=%d", len(tmdb), len(imdb))
    return tmdb, imdb


def merge_data(tmdb_data: List[Dict], imdb_data: List[Dict]) -> pd.DataFrame:
    """Merge TMDB movie records with IMDb rating records on IMDb ID."""
    rows = []
    for m in tmdb_data:
        genres = [g["name"] for g in m.get("genres", [])]
        companies = [c["name"] for c in m.get("production_companies", [])]
        cast = [p["name"] for p in m.get("cast", [])]
        crew = [p["name"] for p in m.get("crew", [])]
        rows.append({
            "imdb_id": m.get("imdb_id"),
            "title": m.get("title"),
            "release_date": m.get("release_date"),
            "runtime": m.get("runtime"),
            "genres": "|".join(genres),
            "budget": m.get("budget"),
            "revenue": m.get("revenue"),
            "tmdb_rating": m.get("vote_average"),
            "tmdb_votes": m.get("vote_count"),
            "cast": "|".join(cast),
            "crew": "|".join(crew),
            "production_companies": "|".join(companies),
            "original_language": m.get("original_language"),
        })

    df_tmdb = pd.DataFrame(rows)
    df_imdb = pd.DataFrame(imdb_data)
    df = df_tmdb.merge(df_imdb, on="imdb_id", how="left")
    logging.info("Merged rows=%d", len(df))
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean merged movie data, standardize types, and remove duplicates."""
    df = df.copy()
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df["release_year"] = df["release_date"].dt.year

    for col in ["budget", "revenue", "runtime", "tmdb_rating", "tmdb_votes", "rating", "num_reviews"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["budget"] = df["budget"].replace(0, pd.NA)
    df["revenue"] = df["revenue"].replace(0, pd.NA)
    df["tmdb_rating"] = df["tmdb_rating"].replace(0, pd.NA)

    df = df.drop_duplicates(subset="imdb_id")
    logging.info("Cleaned rows=%d null_cells=%d", len(df), df.isnull().sum().sum())
    return df


def save_processed_data(df: pd.DataFrame, output_dir: str) -> None:
    """Save processed data as CSV for submission and JSON for local inspection."""
    os.makedirs(output_dir, exist_ok=True)
    csv_path = f"{output_dir}/movies.csv"
    json_path = f"{output_dir}/movies.json"
    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=2, date_format="iso")
    logging.info("Saved %s and %s", csv_path, json_path)
    print(f"Saved {len(df)} rows → {csv_path}")


def main() -> None:
    """Run the data processing step from raw JSON files to processed outputs."""
    tmdb, imdb = load_raw_data()
    df = merge_data(tmdb, imdb)
    df = clean_data(df)
    save_processed_data(df, "data/processed")
    logging.info("Done")


if __name__ == "__main__":
    main()
