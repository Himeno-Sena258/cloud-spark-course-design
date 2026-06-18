FROM m.daocloud.io/docker.io/apache/spark-py:v3.4.0

USER root
COPY spark/analysis_a1.py /opt/spark/work/analysis_a1.py
COPY spark/analysis_a2.py /opt/spark/work/analysis_a2.py
COPY spark/performance_spark.py /opt/spark/work/performance_spark.py
COPY douban_movies.csv /opt/spark/data/douban_movies.csv
RUN chown -R 185:0 /opt/spark/work /opt/spark/data
USER 185
