from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType
import sys

def process_single_file_safely(row):
    """
    處理單一檔案，加入防呆機制。
    如果處理失敗，會記錄錯誤並返回包含錯誤資訊的「模擬資料」。
    """
    file_path = row.path
    file_content = row.content # 這是二進位內容
    
    processed_info_str = None
    status = "UNKNOWN"
    error_msg = None
    
    try:
        # 這裡放置您的核心處理邏輯。
        # 目前仍是簡單地計算二進位內容的長度。
        # 如果未來您加入更複雜的處理，例如解析 DICOM 檔案，
        # 任何在此處發生的錯誤都會被捕獲。
        content_length = len(file_content)
        processed_info_str = f"檔案已處理。內容長度: {content_length} 位元組。"
        
        status = "SUCCESS"
        
    except Exception as e:
        # 發生錯誤時的防呆處理：
        # 1. 設定錯誤狀態和訊息。
        # 2. 將錯誤訊息輸出到 Spark executor 的日誌中 (方便除錯)。
        processed_info_str = "處理失敗。" # 簡潔的處理資訊
        status = "FAILED"
        error_msg = str(e) # 記錄詳細錯誤訊息
        # 輸出到 executor 的標準輸出/錯誤，會反映在 Airflow 任務日誌中
        print(f"錯誤處理檔案 {file_path}: {error_msg}", file=sys.stderr) 
        
    # 返回一個 tuple，其順序和數量必須與 DataFrame 的 schema 定義一致。
    # 這確保即使出錯，也能生成一條有效的記錄。
    return (file_path, processed_info_str, status, error_msg)

def spark_preprocess_spark(input_path, output_path):
    spark = SparkSession.builder.appName("SparkRobustPreprocess").getOrCreate()

    print(f"啟動 Spark 前處理作業，從 {input_path} 到 {output_path}")

    # 讀取輸入文件，將其視為二進位檔案。
    binary_data = spark.read.format("binaryFile").load(input_path)

    # 明確定義輸出 DataFrame 的 Schema，現在包含錯誤處理相關欄位。
    # 這確保了即使某些記錄處理失敗，DataFrame 的結構依然固定。
    output_schema = StructType([
        StructField("file_path", StringType(), True),       # 原始檔案路徑
        StructField("processed_info", StringType(), True),  # 處理結果摘要或簡單訊息
        StructField("status", StringType(), True),          # 處理狀態 (SUCCESS 或 FAILED)
        StructField("error_message", StringType(), True)    # 如果失敗，記錄錯誤訊息
    ])

    # 使用 map 函式調用防呆處理函式。
    # Spark 會並行地對每個檔案調用 process_single_file_safely。
    processed_rdd = binary_data.rdd.map(process_single_file_safely)
    
    # 使用 createDataFrame 並傳入明確的 schema，這可以完全避免型別推斷錯誤。
    processed_data = spark.createDataFrame(processed_rdd, schema=output_schema)

    # 將處理後的數據寫入 S3。
    # 由於現在有多個欄位來記錄狀態和錯誤，建議使用結構化格式如 JSON 或 Parquet。
    # 這裡選擇 JSON，便於您直接查看和理解每條記錄的處理結果。
    processed_data.write.mode("overwrite").json(output_path)

    print("Spark 前處理作業完成。")
    spark.stop()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: spark-submit spark_preprocess.py <input_s3_path> <output_s3_path>")
        sys.exit(1)
    
    input_s3_path = sys.argv[1]
    output_s3_path = sys.argv[2]
    spark_preprocess_spark(input_s3_path, output_s3_path)