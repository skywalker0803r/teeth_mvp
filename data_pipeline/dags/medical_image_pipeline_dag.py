from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# 導入 EMR Serverless Operator
from airflow.providers.amazon.aws.operators.emr import EmrServerlessStartJobOperator

# 定義你的 EMR Serverless Application ID 和 S3 路徑
# 請替換為你實際的 Application ID 和 S3 路徑
EMR_SERVERLESS_APPLICATION_ID = "00fu3tpo0motuq2l" # <--- 替換為你的 EMR Serverless Application ID
SPARK_SCRIPT_S3_PATH = "s3://cji101-28/scripts/spark_preprocess.py" # <--- 替換為你的 spark_preprocess.py 在 S3 上的路徑
INPUT_DATA_S3_PATH = "s3://cji101-28/data/raw_images/" # <--- 替換為你的原始數據在 S3 上的路徑
OUTPUT_DATA_S3_PATH = "s3://cji101-28/data/processed_features/" # <--- 替換為你的處理後數據在 S3 上的路徑
LOG_URI = "s3://cji101-28/log/" # <--- 替換為你的 EMR Serverless 日誌在 S3 上的路徑
AI_INFERENCE_SCRIPT_S3_PATH = "s3://cji101-28/scripts/ai_inference.py" # <--- 替換為你的 ai_inference.py 在 S3 上的路徑
INFERENCE_RESULTS_S3_PATH = "s3://cji101-28/data/inference_results/" # <--- 替換為你的推論結果在 S3 上的路徑
YOUR_EMR_SERVERLESS_EXECUTION_ROLE_ARN = "arn:aws:iam::514246413945:role/emr_s3_admin"

with DAG(
    dag_id='medical_image_pipeline_dag',
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False,
    tags=['medical_imaging', 'etl', 'ai', 'emr-serverless'],
) as dag:
    start_pipeline = BashOperator(
        task_id='start_pipeline',
        bash_command='echo "Starting medical image pipeline..."',
    )

    # Task to run spark_preprocess.py
    preprocess_data = EmrServerlessStartJobOperator(
        task_id="preprocess_medical_images",
        application_id=EMR_SERVERLESS_APPLICATION_ID,
        execution_role_arn=YOUR_EMR_SERVERLESS_EXECUTION_ROLE_ARN,
        job_driver={
            "sparkSubmit": {
                "entryPoint": SPARK_SCRIPT_S3_PATH,
                "entryPointArguments": [INPUT_DATA_S3_PATH, OUTPUT_DATA_S3_PATH],
                "sparkSubmitParameters": "--conf spark.executor.cores=1 --conf spark.executor.memory=1g --conf spark.driver.cores=1 --conf spark.driver.memory=1g"
            }
        },
        configuration_overrides={
            "monitoringConfiguration": {
                "s3MonitoringConfiguration": {"logUri": LOG_URI}
            }
        },
        wait_for_completion=True,
    )

    # Task to run ai_inference.py
    run_ai_inference = EmrServerlessStartJobOperator(
        task_id="run_ai_inference",
        application_id=EMR_SERVERLESS_APPLICATION_ID,
        execution_role_arn=YOUR_EMR_SERVERLESS_EXECUTION_ROLE_ARN,
        job_driver={
            "sparkSubmit": {
                "entryPoint": AI_INFERENCE_SCRIPT_S3_PATH,
                "entryPointArguments": [OUTPUT_DATA_S3_PATH, INFERENCE_RESULTS_S3_PATH],
                "sparkSubmitParameters": "--conf spark.executor.cores=1 --conf spark.executor.memory=1g --conf spark.driver.cores=1 --conf spark.driver.memory=1g"
            }
        },
        configuration_overrides={
            "monitoringConfiguration": {
                "s3MonitoringConfiguration": {"logUri": LOG_URI}
            }
        },
        wait_for_completion=True,
    )

    end_pipeline = BashOperator(
        task_id='end_pipeline',
        bash_command='echo "Medical image pipeline finished."',
    )

    # 定義任務依賴關係
    start_pipeline >> preprocess_data >> run_ai_inference >> end_pipeline