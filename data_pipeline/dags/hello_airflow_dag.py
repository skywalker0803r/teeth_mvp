from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id='hello_airflow_dag',
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['example'],
    ) as dag:
    # 定義一個 BashOperator 任務
    hello_task = BashOperator(
        task_id='print_hello',
        bash_command='echo "Hello Airflow!"',
        )