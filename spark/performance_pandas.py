import argparse
import json
import time
from pathlib import Path

import pandas as pd


def run_query(csv_path: Path) -> tuple[float, int]:
    started = time.perf_counter()

    movies = pd.read_csv(
        csv_path,
        usecols=["movie_id", "rating_score", "genres"],
        low_memory=False,
    )
    movies = movies.dropna(subset=["movie_id", "rating_score", "genres"])
    movies["rating_score"] = pd.to_numeric(movies["rating_score"], errors="coerce")
    movies = movies.dropna(subset=["rating_score"]).drop_duplicates(subset=["movie_id"])

    exploded = movies.assign(genre=movies["genres"].str.split("/")).explode("genre")
    exploded["genre"] = exploded["genre"].str.strip()
    exploded = exploded[(exploded["genre"] != "") & (exploded["genre"] != "Unknown")]

    result = (
        exploded.groupby("genre", as_index=False)
        .agg(movie_count=("movie_id", "nunique"), avg_rating=("rating_score", "mean"))
        .sort_values(["movie_count", "avg_rating"], ascending=[False, False])
    )

    # Materialize the result before stopping the timer.
    result_records = result.to_dict("records")
    elapsed = time.perf_counter() - started
    return elapsed, len(result_records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "douban_movies.csv",
    )
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "performance_pandas.json",
    )
    args = parser.parse_args()

    durations = []
    result_rows = 0
    for run_number in range(1, args.runs + 1):
        elapsed, result_rows = run_query(args.csv)
        durations.append(elapsed)
        print(f"Pandas run {run_number}: {elapsed:.4f} s")

    summary = {
        "engine": "pandas",
        "executors": 0,
        "runs_seconds": durations,
        "average_seconds": sum(durations) / len(durations),
        "result_rows": result_rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("A3_RESULT_JSON=" + json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
