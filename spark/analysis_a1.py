from pyspark.sql import SparkSession
from pyspark.sql import functions as F


DATA_PATH = "/opt/spark/data/douban_movies.csv"


spark = SparkSession.builder.appName("DoubanMovieCleaning").getOrCreate()

raw = (
    spark.read.option("header", True)
    .option("inferSchema", True)
    .option("multiLine", True)
    .option("quote", '"')
    .option("escape", '"')
    .csv(DATA_PATH)
)

print("=== Schema ===")
raw.printSchema()

print("=== First 5 rows ===")
raw.show(5, truncate=40)

row_count_before = raw.count()
print(f"=== Row count before cleaning: {row_count_before} ===")

print("=== Missing-value counts and ratios ===")
missing_expressions = []
for column in raw.columns:
    missing = F.sum(
        F.when(F.col(column).isNull() | (F.trim(F.col(column).cast("string")) == ""), 1).otherwise(0)
    )
    missing_expressions.extend(
        [
            missing.alias(f"{column}_missing"),
            F.round(missing / F.lit(row_count_before) * 100, 2).alias(f"{column}_missing_pct"),
        ]
    )
raw.agg(*missing_expressions).show(vertical=True, truncate=False)

# Strategy 1: rows without key analytical fields cannot support rating analysis.
cleaned = raw.dropna(subset=["movie_id", "title", "year", "rating_score"])

# Strategy 2: descriptive fields can retain the record with explicit placeholders.
cleaned = cleaned.fillna(
    {
        "original_title": "未知",
        "genres": "未知",
        "countries": "未知",
        "directors": "未知",
        "summary": "暂无简介",
    }
)

cleaned = (
    cleaned.withColumn("year", F.col("year").cast("int"))
    .withColumn("rating_score", F.col("rating_score").cast("double"))
    .withColumn("rating_count", F.col("rating_count").cast("long"))
    .withColumn("collect_count", F.col("collect_count").cast("long"))
    .dropDuplicates(["movie_id"])
)

row_count_after = cleaned.count()
print(f"=== Row count after cleaning: {row_count_after} ===")
print(f"=== Removed rows: {row_count_before - row_count_after} ===")

print("=== Numeric statistics after cleaning ===")
cleaned.select("year", "rating_score", "rating_count", "collect_count").describe().show(
    truncate=False
)

print("=== Cleaned sample ===")
cleaned.select(
    "movie_id", "title", "year", "rating_score", "genres", "countries", "directors"
).show(10, truncate=30)

spark.stop()
