import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from web.operators.Web_To_GCS_Hook import WebToGCSHKOperator
from airflow.providers.google.cloud.transfers.gcs_to_local import GCSToLocalFilesystemOperator
from airflow.operators.python import PythonOperator
from web.operators.PG_db_ingestion import db_conn_ingestion


AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")


PG_HOST = os.getenv('PG_HOST')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_PORT = os.getenv('PG_PORT')
PG_DATABASE = os.getenv('PG_DATABASE')

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")
ENDPOINT = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/'
SERVICE = "green"
OBJECT = SERVICE+'_tripdata_{{ dag_run.logical_date.strftime(\'%Y-%m\') }}.csv.gz'
FILE_NAME = SERVICE+'_tripdata_{{ dag_run.logical_date.strftime(\'%Y-%m\') }}.csv'
PATH_TO_SAVED_FILE = f"{AIRFLOW_HOME}/{FILE_NAME}"
TABLE_NAME_TEMPLATE = SERVICE+'_taxi_data'
#green_taxi_data

DEFAULT_ARGS = {
    "owner": "airflow",
    "start_date": datetime(2019, 1, 1),
    "email": [os.getenv("ALERT_EMAIL", "")],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="Load-Green-Taxi-Data-Web-To-GCS-To-Postgres",
    description="Job to move data from website to Google Cloud Storage and then from GCS to Postgres Database",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 6 2 * *",
    max_active_runs=1,
    catchup=True,
    tags=["Website-to-GCS-Bucket-to-PG"]
) as dag:
    download_to_gcs= WebToGCSHKOperator(
		task_id="extract_from_web_to_gcs",
		endpoint=ENDPOINT,
		destination_path=OBJECT,
		destination_bucket=BUCKET,
		service=SERVICE
    )
    download_file = GCSToLocalFilesystemOperator(
		task_id="download_file_from_gcs",
		object_name=SERVICE+"/"+FILE_NAME,
		bucket=BUCKET,
		filename=PATH_TO_SAVED_FILE
    )
    ingestion_data = PythonOperator(
        task_id ="load_data_to_PD_DB",
        python_callable=db_conn_ingestion,
        op_kwargs=dict(
            user=PG_USER,
            password=PG_PASSWORD,
            host=PG_HOST,
            port=PG_PORT,
            db=PG_DATABASE,
            table_name=TABLE_NAME_TEMPLATE,
            csv_file=PATH_TO_SAVED_FILE
            )
        )
    delete_file = BashOperator(
      	task_id = "delete_file",
      	bash_command = f'rm {PATH_TO_SAVED_FILE}'
    )

    download_to_gcs >> download_file >> ingestion_data >> delete_file


