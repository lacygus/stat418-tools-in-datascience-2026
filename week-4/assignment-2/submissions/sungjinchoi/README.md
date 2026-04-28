# Movie Data Collection & Analysis Pipeline

## Overview

Collects movie data from the TMDB API and IMDb rating sources, then analyzes trends.

50 movies. TMDB provides metadata, and IMDb provides ratings and vote counts.

---

## Setup

### 1. Get TMDB API key

Create account at https://www.themoviedb.org/ → Settings → API → Request key (free).

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set TMDB_API_KEY=your_key_here
```

### 3. Install dependencies

```bash
uv pip install -r requirements.txt
```

---

## Run

Full pipeline:

```bash
python run_pipeline.py
```

Or run steps individually:

```bash
python api_collector.py    # collect TMDB data
python web_scraper.py      # scrape IMDb ratings
python data_processor.py   # merge and clean
python analyze_data.py     # analyze and generate REPORT.md
```

---

## Output

```
data/raw/tmdb/movies.json         raw TMDB responses
data/raw/imdb/ratings.json        IMDb ratings
data/processed/movies.csv         merged, cleaned dataset
data/analysis/rating_analysis.png
data/analysis/genre_analysis.png
data/analysis/financial_analysis.png
data/analysis/temporal_analysis.png
REPORT.md                         generated analysis report
logs/pipeline.log
```

---

## Data Sources

- TMDB API: title, genres, budget, revenue, runtime, cast, ratings
- IMDb: rating, vote count, and metascore when available. The scraper checks IMDb pages first and uses IMDb's public ratings dataset as a fallback when page HTML does not expose ratings.

---

## Ethical Considerations

- IMDb robots.txt checked before page scraping
- Rate limiting: 2s between IMDb requests, 0.25s between TMDB requests
- User-Agent identifies as student project
- Data used for educational purposes only

---

## Known Limitations

- Budget/revenue missing for many titles (TMDB returns 0 when unknown)
- IMDb metascore may be missing for some entries due to dynamic rendering
- IMDb page HTML may not expose ratings consistently, so the pipeline falls back to IMDb's public ratings dataset for rating and vote count fields
- Dataset limited to 50 movies from TMDB "popular" list
