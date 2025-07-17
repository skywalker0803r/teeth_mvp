from pyspark.sql import SparkSession

if __name__ == "__main__":
    spark = SparkSession.builder.appName("HelloSpark").getOrCreate()
    print("Hello from Spark!")
    spark.stop()