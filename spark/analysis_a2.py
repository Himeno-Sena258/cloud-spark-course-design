from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


DATA_PATH = "/opt/spark/data/douban_movies.csv"


spark = SparkSession.builder.appName("DoubanMovieAnalysis").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

raw = (
    spark.read.option("header", True)
    .option("inferSchema", True)
    .option("multiLine", True)
    .option("quote", '"')
    .option("escape", '"')
    .csv(DATA_PATH)
)

movies = (
    raw.dropna(subset=["movie_id", "title", "year", "rating_score"])
    .fillna(
        {
            "genres": "Unknown",
            "countries": "Unknown",
            "directors": "Unknown",
        }
    )
    .withColumn("year", F.col("year").cast("int"))
    .withColumn("rating_score", F.col("rating_score").cast("double"))
    .withColumn("rating_count", F.coalesce(F.col("rating_count").cast("long"), F.lit(0)))
    .withColumn("collect_count", F.coalesce(F.col("collect_count").cast("long"), F.lit(0)))
    .filter(F.col("year").between(1880, 2030))
    .filter(F.col("rating_score").between(0, 10))
    .dropDuplicates(["movie_id"])
    .cache()
)

movies.createOrReplaceTempView("movies")
print(f"=== A2_DATASET_ROWS: {movies.count()} ===")

# Query 1: GROUP BY aggregation after splitting multi-valued genre fields.
genre_stats = (
    movies.select(
        "movie_id",
        "rating_score",
        "rating_count",
        F.explode(F.split(F.col("genres"), "/")).alias("genre"),
    )
    .withColumn("genre", F.trim("genre"))
    .filter((F.col("genre") != "") & (F.col("genre") != "Unknown"))
    .groupBy("genre")
    .agg(
        F.countDistinct("movie_id").alias("movie_count"),
        F.round(F.avg("rating_score"), 2).alias("avg_rating"),
        F.sum("rating_count").alias("total_rating_count"),
    )
    .orderBy(F.desc("movie_count"), F.desc("avg_rating"))
)

print("=== A2_QUERY_1_GROUP_BY_GENRE ===")
genre_stats.show(20, truncate=False)

# Query 2: ORDER BY Top-N. A popularity threshold avoids obscure titles with
# very few ratings dominating the ranking.
top_rated = (
    movies.filter(F.col("rating_count") >= 1000)
    .select("title", "year", "rating_score", "rating_count", "genres", "countries")
    .orderBy(F.desc("rating_score"), F.desc("rating_count"))
    .limit(10)
)

print("=== A2_QUERY_2_TOP_10_RATED_MOVIES ===")
top_rated.show(10, truncate=35)

# Query 3: time trend by decade.
decade_trend = (
    movies.withColumn("decade", (F.floor(F.col("year") / 10) * 10).cast("int"))
    .groupBy("decade")
    .agg(
        F.count("*").alias("movie_count"),
        F.round(F.avg("rating_score"), 2).alias("avg_rating"),
        F.round(F.avg("rating_count"), 0).cast("long").alias("avg_rating_count"),
    )
    .filter(F.col("decade").between(1880, 2030))
    .orderBy("decade")
)

print("=== A2_QUERY_3_DECADE_TREND ===")
decade_trend.show(30, truncate=False)

# Query 4: window function. Rank the top three sufficiently reviewed movies
# within each decade.
rank_window = Window.partitionBy("decade").orderBy(
    F.desc("rating_score"), F.desc("rating_count")
)
decade_top3 = (
    movies.withColumn("decade", (F.floor(F.col("year") / 10) * 10).cast("int"))
    .filter(F.col("rating_count") >= 1000)
    .withColumn("rank_in_decade", F.row_number().over(rank_window))
    .filter(F.col("rank_in_decade") <= 3)
    .select(
        "decade",
        "rank_in_decade",
        "title",
        "year",
        "rating_score",
        "rating_count",
    )
    .orderBy(F.desc("decade"), "rank_in_decade")
)

print("=== A2_QUERY_4_WINDOW_TOP_3_PER_DECADE ===")
decade_top3.show(30, truncate=35)

# Query 5: JOIN each movie with its decade average, then find movies whose
# ratings exceed the corresponding decade benchmark by the largest margin.
movie_decades = movies.withColumn(
    "decade", (F.floor(F.col("year") / 10) * 10).cast("int")
)
decade_average = movie_decades.groupBy("decade").agg(
    F.avg("rating_score").alias("decade_avg_rating")
)
above_decade_average = (
    movie_decades.join(decade_average, on="decade", how="inner")
    .filter(F.col("rating_count") >= 1000)
    .withColumn(
        "rating_above_decade_avg",
        F.round(F.col("rating_score") - F.col("decade_avg_rating"), 2),
    )
    .select(
        "title",
        "year",
        "decade",
        "rating_score",
        F.round("decade_avg_rating", 2).alias("decade_avg_rating"),
        "rating_above_decade_avg",
        "rating_count",
    )
    .orderBy(F.desc("rating_above_decade_avg"), F.desc("rating_count"))
    .limit(10)
)

print("=== A2_QUERY_5_JOIN_ABOVE_DECADE_AVERAGE ===")
above_decade_average.show(10, truncate=35)

movies.unpersist()
spark.stop()
