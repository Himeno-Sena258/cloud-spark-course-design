import json
import time

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


DATA_PATH = "/opt/spark/data/douban_movies.csv"
RUNS = 3


spark = SparkSession.builder.appName("DoubanPerformanceTest").getOrCreate()
spark.sparkContext.setLogLevel("WARN")


def run_query() -> tuple[float, int]:
    started = time.perf_counter()

    movies = (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .option("multiLine", True)
        .option("quote", '"')
        .option("escape", '"')
        .csv(DATA_PATH)
        .select("movie_id", "rating_score", "genres")
        .dropna(subset=["movie_id", "rating_score", "genres"])
        .withColumn("rating_score", F.col("rating_score").cast("double"))
        .dropna(subset=["rating_score"])
        .dropDuplicates(["movie_id"])
    )

    result = (
        movies.select(
            "movie_id",
            "rating_score",
            F.explode(F.split(F.col("genres"), "/")).alias("genre"),
        )
        .withColumn("genre", F.trim("genre"))
        .filter((F.col("genre") != "") & (F.col("genre") != "Unknown"))
        .groupBy("genre")
        .agg(
            F.countDistinct("movie_id").alias("movie_count"),
            F.avg("rating_score").alias("avg_rating"),
        )
        .orderBy(F.desc("movie_count"), F.desc("avg_rating"))
    )

    result_rows = len(result.collect())
    elapsed = time.perf_counter() - started
    return elapsed, result_rows


durations = []
result_rows = 0
for run_number in range(1, RUNS + 1):
    elapsed, result_rows = run_query()
    durations.append(elapsed)
    print(f"Spark run {run_number}: {elapsed:.4f} s")

executors = int(spark.conf.get("spark.executor.instances", "1"))
summary = {
    "engine": "pyspark",
    "executors": executors,
    "runs_seconds": durations,
    "average_seconds": sum(durations) / len(durations),
    "result_rows": result_rows,
}
print("A3_RESULT_JSON=" + json.dumps(summary, ensure_ascii=False))

spark.stop()
