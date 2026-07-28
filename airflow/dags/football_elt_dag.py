from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import docker

default_args = {
    'owner': 'football_admin',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def run_command_in_pipeline(command, workdir=None):
    # Kết nối tới docker daemon thông qua docker.sock
    client = docker.from_env()
    container = client.containers.get('football_pipeline')
    
    print(f"Executing command: {command} in container football_pipeline (workdir: {workdir})")
    exec_log = container.exec_run(command, workdir=workdir)
    output = exec_log.output.decode('utf-8', errors='ignore')
    print(output)
    
    if exec_log.exit_code != 0:
        raise Exception(f"Command '{command}' failed with exit code {exec_log.exit_code}")

def run_weekly_scrape():
    run_command_in_pipeline('python weekly.py', workdir='/app')

def run_dbt_transform():
    run_command_in_pipeline('dbt run --profiles-dir /app/dbt_project', workdir='/app/dbt_project')

def run_ml_train():
    run_command_in_pipeline('python train.py', workdir='/app/ml_predictor')

with DAG(
    'football_weekly_elt_pipeline',
    default_args=default_args,
    description='Pipeline cào trận lẻ hàng tuần, dbt transform và huấn luyện lại ML tự động',
    schedule_interval='0 3 * * 1', # Chạy vào 3:00 sáng Thứ Hai hàng tuần
    catchup=False,
) as dag:

    task_scrape = PythonOperator(
        task_id='scrape_weekly_data',
        python_callable=run_weekly_scrape,
    )

    task_dbt = PythonOperator(
        task_id='run_dbt_transform',
        python_callable=run_dbt_transform,
    )

    task_train = PythonOperator(
        task_id='retrain_ml_model',
        python_callable=run_ml_train,
    )

    task_scrape >> task_dbt >> task_train
