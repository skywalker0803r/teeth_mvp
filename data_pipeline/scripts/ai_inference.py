from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import StructType, StructField, StringType
import sys

def perform_inference_safely(row):
    """
    對單一記錄執行模擬 AI 推論，加入防呆機制。
    如果推論過程出錯，會記錄錯誤並返回包含錯誤資訊的「模擬結果」。
    """
    file_path = row.file_path
    processed_info = row.processed_info # 從上游 spark_preprocess 傳來的處理資訊
    
    inference_result_str = None
    status = "UNKNOWN"
    error_msg = None
    
    try:
        # === 這裡放置您的核心 AI 推論邏輯。===
        # 目前仍是簡單的字串處理，模擬推論。
        # 如果未來您集成真正的 AI 模型 (例如，呼叫 PyTorch 或 TensorFlow)，
        # 任何在此處發生的錯誤 (如模型載入失敗、推論計算異常) 都會被捕獲。
        
        # 假設 processed_info 是模型所需的特徵數據
        # 模擬一個推論過程，例如，根據 processed_info 的內容生成一個結果
        inference_result_str = f"AI 推論結果: 針對 '{processed_info}' 偵測到特定模式。"
        
        status = "SUCCESS"
        
    except Exception as e:
        # 發生錯誤時的防呆處理：
        # 1. 設定錯誤狀態和訊息。
        # 2. 將錯誤訊息輸出到 Spark executor 的日誌中 (方便除錯)。
        inference_result_str = "AI 推論失敗。" # 簡潔的推論結果
        status = "FAILED"
        error_msg = str(e) # 記錄詳細錯誤訊息
        # 輸出到 executor 的標準輸出/錯誤，這將反映在 Airflow 或 EMR Serverless 的任務日誌中
        print(f"錯誤執行推論在檔案 {file_path} (processed_info: '{processed_info}'): {error_msg}", file=sys.stderr)
        
    # 返回一個 tuple，其順序和數量必須與 DataFrame 的 schema 定義一致。
    # 這確保即使出錯，也能生成一條有效的記錄。
    return (file_path, inference_result_str, status, error_msg)

def ai_inference_spark(input_path, output_path):
    spark = SparkSession.builder.appName("AIInferenceRobust").getOrCreate()

    print(f"啟動 AI 推論作業 (防呆強化版)，從 {input_path} 到 {output_path}")

    # 讀取 spark_preprocess.py 輸出路徑中的 JSON 檔案
    # Spark 會根據 JSON 內容自動推斷 schema，這應該會匹配預處理腳本的輸出結構
    input_data = spark.read.json(input_path)

    # 選擇需要進行推論的欄位，並過濾成功處理的記錄。
    # 僅處理上游預處理成功的數據，這本身也是一種防呆。
    successful_data = input_data.filter(col("status") == "SUCCESS")

    # === 修改點: 使用 map 函式調用防呆推論函式 ===
    # Spark 會並行地對每個「成功」的檔案記錄調用 perform_inference_safely。
    inference_rdd = successful_data.rdd.map(perform_inference_safely)
    
    # 明確定義輸出 DataFrame 的 Schema。
    # 現在包含原始檔案路徑、推論結果、推論狀態和錯誤訊息。
    output_inference_schema = StructType([
        StructField("file_path", StringType(), True),       # 原始檔案路徑
        StructField("inference_result", StringType(), True),# AI 推論結果摘要或錯誤訊息
        StructField("status", StringType(), True),          # 推論狀態 (SUCCESS 或 FAILED)
        StructField("error_message", StringType(), True)    # 如果失敗，記錄錯誤訊息
    ])

    # 使用 createDataFrame 並傳入明確的 schema，避免任何型別推斷錯誤。
    inference_results = spark.createDataFrame(inference_rdd, schema=output_inference_schema)

    # 將推論結果寫入 S3。
    # 由於輸出是結構化的多欄位數據，建議使用 JSON 或 Parquet 格式。
    inference_results.write.mode("overwrite").json(output_path)

    print("AI 推論作業完成。")
    spark.stop()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: spark-submit ai_inference.py <input_s3_path> <output_s3_path>")
        sys.exit(1)
    
    input_s3_path = sys.argv[1]
    output_s3_path = sys.argv[2]
    ai_inference_spark(input_s3_path, output_s3_path)