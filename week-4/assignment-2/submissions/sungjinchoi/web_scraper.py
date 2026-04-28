#!/usr/bin/env python3
import gzip
import io
import json
import logging
import os
import time
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/web_scraper.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

HEADERS = {"User-Agent": "UCLA STAT418 Student - sungjinchoi5790@gmail.com"}
IMDB_RATINGS_URL = "https://datasets.imdbws.com/title.ratings.tsv.gz"


class IMDbScraper:
    """Collect IMDb rating information using page scraping and a dataset fallback."""

    def __init__(self, delay: float = 2.0) -> None:
        """Initialize the scraper with a rate limit delay and student User-Agent."""
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def check_robots_txt(self) -> bool:
        """Check IMDb robots.txt before attempting page scraping."""
        try:
            r = self.session.get("https://www.imdb.com/robots.txt", timeout=10)
            disallowed = "Disallow: /" in r.text
            logging.info("robots.txt checked — disallowed=%s", disallowed)
            return not disallowed
        except requests.RequestException as e:
            logging.error("robots.txt check failed: %s", e)
            return False

    def scrape_movie_page(self, imdb_id: str) -> Dict:
        """Scrape rating, vote count, and metascore fields from one IMDb title page."""
        time.sleep(self.delay)
        url = f"https://www.imdb.com/title/{imdb_id}/"
        try:
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, "lxml")
            data = {
                "imdb_id": imdb_id,
                "rating": self._extract_rating(soup),
                "num_reviews": self._extract_review_count(soup),
                "metascore": self._extract_metascore(soup),
            }
            logging.info("Scraped %s rating=%s", imdb_id, data["rating"])
            return data
        except Exception as e:
            logging.error("Error scraping %s: %s", imdb_id, e)
            return {"imdb_id": imdb_id, "rating": None, "num_reviews": None, "metascore": None}

    def _extract_rating(self, soup: BeautifulSoup) -> float | None:
        """Extract the IMDb rating from JSON-LD structured data when available."""
        tag = soup.find("script", type="application/ld+json")
        if tag:
            try:
                d = json.loads(tag.string)
                val = d.get("aggregateRating", {}).get("ratingValue")
                return float(val) if val else None
            except Exception:
                pass
        return None

    def _extract_review_count(self, soup: BeautifulSoup) -> int | None:
        """Extract the IMDb vote count from JSON-LD structured data when available."""
        tag = soup.find("script", type="application/ld+json")
        if tag:
            try:
                d = json.loads(tag.string)
                val = d.get("aggregateRating", {}).get("ratingCount")
                return int(val) if val else None
            except Exception:
                pass
        return None

    def _extract_metascore(self, soup: BeautifulSoup) -> int | None:
        """Extract the Metascore from the page when IMDb includes it in the HTML."""
        tag = soup.find("span", attrs={"data-testid": "metacritic-score-box"})
        if not tag:
            tag = soup.find("span", class_=lambda c: c and "metacritic" in c.lower())
        if tag:
            try:
                return int(tag.get_text(strip=True))
            except Exception:
                pass
        return None

    def scrape_multiple_movies(self, imdb_ids: List[str]) -> List[Dict]:
        """Scrape IMDb pages for a list of IMDb title identifiers."""
        results = []
        for i, iid in enumerate(imdb_ids, 1):
            print(f"  [{i}/{len(imdb_ids)}] {iid}")
            results.append(self.scrape_movie_page(iid))
        return results

    def fetch_public_ratings_dataset(self, imdb_ids: List[str]) -> List[Dict]:
        """Fetch IMDb public ratings dataset as a fallback when pages are blocked."""
        wanted = set(imdb_ids)
        results = {
            imdb_id: {"imdb_id": imdb_id, "rating": None, "num_reviews": None, "metascore": None}
            for imdb_id in imdb_ids
        }

        response = self.session.get(IMDB_RATINGS_URL, timeout=60)
        response.raise_for_status()

        with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz:
            for raw_line in gz:
                line = raw_line.decode("utf-8").strip()
                if not line or line.startswith("tconst"):
                    continue

                imdb_id, rating, votes = line.split("\t")
                if imdb_id in wanted:
                    results[imdb_id] = {
                        "imdb_id": imdb_id,
                        "rating": float(rating),
                        "num_reviews": int(votes),
                        "metascore": None,
                    }

        logging.info("Loaded IMDb public ratings fallback for %d ids", len(wanted))
        return [results[imdb_id] for imdb_id in imdb_ids]


def main() -> None:
    """Run IMDb collection and save raw rating records to JSON."""
    os.makedirs("data/raw/imdb", exist_ok=True)

    with open("data/raw/tmdb/movies.json") as f:
        movies = json.load(f)

    imdb_ids = [m["imdb_id"] for m in movies if m.get("imdb_id")]
    if not imdb_ids:
        raise SystemExit("ERROR: No IMDb IDs found in TMDB data")

    scraper = IMDbScraper()
    allowed = scraper.check_robots_txt()
    if not allowed:
        print("Note: robots.txt restricts scraping — proceeding with minimal rate for educational use")

    print(f"Scraping {len(imdb_ids)} IMDb pages...")
    results = scraper.scrape_multiple_movies(imdb_ids)
    if not any(row.get("rating") is not None for row in results):
        print("IMDb pages did not expose ratings. Using IMDb public ratings dataset fallback...")
        results = scraper.fetch_public_ratings_dataset(imdb_ids)

    out = "data/raw/imdb/ratings.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {len(results)} IMDb records → {out}")
    logging.info("Done: %d records saved", len(results))


if __name__ == "__main__":
    main()
