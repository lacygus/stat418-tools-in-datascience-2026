#!/usr/bin/env python3
import logging
import os
from typing import Dict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/analyze_data.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

ANALYSIS_DIR = "data/analysis"


def load_data() -> pd.DataFrame:
    """Load the processed movie dataset for analysis."""
    df = pd.read_csv("data/processed/movies.csv", parse_dates=["release_date"])
    logging.info("Loaded %d rows", len(df))
    return df


def rating_analysis(df: pd.DataFrame) -> Dict:
    """Analyze TMDB and IMDb rating distributions and correlation."""
    d = df[["tmdb_rating", "rating"]].dropna()
    corr = d["tmdb_rating"].corr(d["rating"])

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].scatter(d["tmdb_rating"], d["rating"], alpha=0.6, color="steelblue")
    axes[0].set_xlabel("TMDB Rating")
    axes[0].set_ylabel("IMDb Rating")
    axes[0].set_title(f"TMDB vs IMDb Ratings  (r={corr:.2f})")

    axes[1].hist(d["tmdb_rating"], bins=20, alpha=0.6, label="TMDB", color="steelblue")
    axes[1].hist(d["rating"], bins=20, alpha=0.6, label="IMDb", color="coral")
    axes[1].set_title("Rating Distributions")
    axes[1].legend()

    plt.tight_layout()
    path = f"{ANALYSIS_DIR}/rating_analysis.png"
    plt.savefig(path, dpi=150)
    plt.close()
    logging.info("Saved %s  corr=%.3f", path, corr)

    return {
        "corr": round(corr, 3),
        "tmdb_mean": round(d["tmdb_rating"].mean(), 2),
        "imdb_mean": round(d["rating"].mean(), 2),
        "n": len(d),
    }


def genre_analysis(df: pd.DataFrame) -> Dict:
    """Analyze genre frequency and average TMDB rating by genre."""
    rows = []
    for _, r in df.iterrows():
        for g in str(r["genres"]).split("|"):
            g = g.strip()
            if g and g != "nan":
                rows.append({"genre": g, "tmdb_rating": r["tmdb_rating"]})
    gdf = pd.DataFrame(rows)

    top_genres = gdf["genre"].value_counts().head(10)
    avg_by_genre = (
        gdf.groupby("genre")["tmdb_rating"]
        .mean()
        .dropna()
        .sort_values(ascending=False)
        .head(10)
    )

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    top_genres.plot(kind="barh", ax=axes[0], color="steelblue")
    axes[0].set_title("Top 10 Genres by Count")
    axes[0].set_xlabel("Count")
    axes[0].invert_yaxis()

    avg_by_genre.plot(kind="barh", ax=axes[1], color="coral")
    axes[1].set_title("Avg TMDB Rating by Genre")
    axes[1].set_xlabel("Avg Rating")
    axes[1].invert_yaxis()

    plt.tight_layout()
    path = f"{ANALYSIS_DIR}/genre_analysis.png"
    plt.savefig(path, dpi=150)
    plt.close()
    logging.info("Saved %s", path)

    return {
        "top_genre": top_genres.index[0],
        "top_genre_count": int(top_genres.iloc[0]),
        "best_rated_genre": avg_by_genre.index[0],
        "best_rated_avg": round(avg_by_genre.iloc[0], 2),
    }


def financial_analysis(df: pd.DataFrame) -> Dict:
    """Analyze budget, revenue, and profit relationships for movies with financial data."""
    d = df[["title", "budget", "revenue", "tmdb_rating"]].dropna(subset=["budget", "revenue"])
    d = d[d["budget"] > 0].copy()
    d["profit"] = d["revenue"] - d["budget"]
    corr = d["budget"].corr(d["revenue"])

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].scatter(d["budget"] / 1e6, d["revenue"] / 1e6, alpha=0.6, color="steelblue")
    axes[0].set_xlabel("Budget ($M)")
    axes[0].set_ylabel("Revenue ($M)")
    axes[0].set_title(f"Budget vs Revenue  (r={corr:.2f})")

    top10 = d.nlargest(10, "profit")
    axes[1].barh(top10["title"], top10["profit"] / 1e6, color="coral")
    axes[1].set_xlabel("Profit ($M)")
    axes[1].set_title("Top 10 Most Profitable Movies")
    axes[1].invert_yaxis()

    plt.tight_layout()
    path = f"{ANALYSIS_DIR}/financial_analysis.png"
    plt.savefig(path, dpi=150)
    plt.close()
    logging.info("Saved %s  corr=%.3f", path, corr)

    most_profitable = d.loc[d["profit"].idxmax(), "title"]
    return {
        "corr": round(corr, 3),
        "most_profitable": most_profitable,
        "n": len(d),
    }


def temporal_analysis(df: pd.DataFrame) -> Dict:
    """Analyze movie counts and average ratings by release year."""
    d = df.dropna(subset=["release_year", "tmdb_rating"])
    d = d[d["release_year"] >= 2000].copy()
    yearly = d.groupby("release_year").agg(
        count=("title", "count"),
        avg_rating=("tmdb_rating", "mean"),
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].bar(yearly.index, yearly["count"], color="steelblue")
    axes[0].set_title("Movies per Year")
    axes[0].set_xlabel("Year")
    axes[0].set_ylabel("Count")

    axes[1].plot(yearly.index, yearly["avg_rating"], marker="o", color="coral")
    axes[1].set_title("Avg TMDB Rating by Year")
    axes[1].set_xlabel("Year")
    axes[1].set_ylabel("Avg Rating")

    plt.tight_layout()
    path = f"{ANALYSIS_DIR}/temporal_analysis.png"
    plt.savefig(path, dpi=150)
    plt.close()
    logging.info("Saved %s", path)

    peak_year = int(yearly["count"].idxmax())
    return {
        "peak_year": peak_year,
        "peak_count": int(yearly.loc[peak_year, "count"]),
    }


def write_report(df: pd.DataFrame, stats: Dict) -> None:
    """Write a Markdown report summarizing the analysis and generated figures."""
    r = stats["rating"]
    g = stats["genre"]
    f = stats["financial"]
    t = stats["temporal"]

    imdb_matched = df["rating"].notna().sum()

    report = f"""# Movie Data Collection & Analysis Report

**Data:** TMDB API + IMDb scraping
**Generated:** {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}
**Total records:** {len(df)}

---

## 1. Data Collection Summary

| Source | Records | Method |
|--------|---------|--------|
| TMDB API | {len(df)} | REST API (popular endpoint) |
| IMDb matched | {imdb_matched} | IMDb pages + public ratings fallback |

Collected top-50 popular movies from TMDB. IMDb ratings were merged on IMDb ID.

---

## 2. Rating Analysis

Correlation between TMDB and IMDb ratings: **{r['corr']}**

| Platform | Mean Rating | Matched pairs |
|----------|-------------|---------------|
| TMDB | {r['tmdb_mean']} | — |
| IMDb | {r['imdb_mean']} | {r['n']} |

![Rating Analysis](data/analysis/rating_analysis.png)

TMDB and IMDb ratings are closely correlated. Both platforms score popular titles similarly.

---

## 3. Genre Analysis

Most common genre: **{g['top_genre']}** ({g['top_genre_count']} movies)
Highest rated genre: **{g['best_rated_genre']}** (avg {g['best_rated_avg']})

![Genre Analysis](data/analysis/genre_analysis.png)

Action and Drama dominate the popular list. Genre count doesn't predict rating — niche genres can outperform mainstream ones.

---

## 4. Financial Analysis

Budget vs revenue correlation: **{f['corr']}** (n={f['n']})
Most profitable movie: **{f['most_profitable']}**

![Financial Analysis](data/analysis/financial_analysis.png)

Higher budget generally predicts higher revenue. But many high-budget films still underperform.

---

## 5. Temporal Analysis

Most productive year in dataset: **{t['peak_year']}** ({t['peak_count']} movies)

![Temporal Analysis](data/analysis/temporal_analysis.png)

Recent years dominate the popular list. Ratings trend slightly downward for very recent releases — likely fewer votes so far.

---

## 6. Challenges

- IMDb pages can return limited HTML or hide rating data. The scraper first checks pages and then uses IMDb's public ratings dataset as a fallback for ratings and vote counts.
- TMDB returns `0` for budget/revenue when unknown. Treated as missing.
- Some TMDB movies lack an IMDb ID — those rows have null IMDb columns.

---

## 7. Limitations

- 50 movies from TMDB "popular" list only — skewed toward recent blockbusters.
- Metascore extraction is unreliable due to IMDb's dynamic content.
- Budget/revenue available for only {f['n']} movies.
"""

    with open("REPORT.md", "w", encoding="utf-8") as out:
        out.write(report)
    logging.info("Wrote REPORT.md")
    print("Wrote REPORT.md")


def main() -> None:
    """Run all analysis steps and regenerate the Markdown report."""
    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    df = load_data()
    stats = {
        "rating": rating_analysis(df),
        "genre": genre_analysis(df),
        "financial": financial_analysis(df),
        "temporal": temporal_analysis(df),
    }
    write_report(df, stats)
    logging.info("Done")


if __name__ == "__main__":
    main()
