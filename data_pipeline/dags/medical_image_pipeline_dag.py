from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

with DAG(
    dag_id='medical_image_pipeline_dag',
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False,
    tags=['medical_imaging', 'etl', 'ai'],
) as dag:
    start_pipeline = BashOperator(
        task_id='start_pipeline',
        bash_command='echo "Starting medical image pipeline..."',
    )

    # 執行 Spark 影像前處理
    # 注意：這裡我們直接執行 Python 腳本來模擬 Spark 處理
    # 在實際生產環境中，你會使用 SparkSubmitOperator 或其他方式提交 Spark 任務到 Spark 集群
    spark_preprocess_task = BashOperator(
        task_id='spark_preprocess_task',
        bash_command='python /opt/airflow/scripts/spark_preprocess.py /opt/airflow/data/raw_images /opt/airflow/data/processed_features',
    )

    # 執行 AI 模型推論
    ai_inference_task = BashOperator(
        task_id='ai_inference_task',
        bash_command='python /opt/airflow/scripts/ai_inference.py /opt/airflow/data/processed_features /opt/airflow/data/inference_results',
    )

    end_pipeline = BashOperator(
        task_id='end_pipeline',
        bash_command='echo "Medical image pipeline finished."',
    )

    # 定義任務依賴關係
    start_pipeline >> spark_preprocess_task >> ai_inference_task >> end_pipeline
