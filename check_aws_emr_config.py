import boto3
import os
import sys
import uuid
from urllib.parse import urlparse

# --- Configuration from your Airflow DAG ---
EMR_SERVERLESS_APPLICATION_ID = "00fu3tpo0motuq2l"
SPARK_SCRIPT_S3_PATH = "s3://cji101-28/scripts/spark_preprocess.py"
INPUT_DATA_S3_PATH = "s3://cji101-28/data/raw_images/"
OUTPUT_DATA_S3_PATH = "s3://cji101-28/data/processed_features/"
LOG_URI = "s3://cji101-28/log/"
AI_INFERENCE_SCRIPT_S3_PATH = "s3://cji101-28/scripts/ai_inference.py"
INFERENCE_RESULTS_S3_PATH = "s3://cji101-28/data/inference_results/"
EMR_EXECUTION_ROLE_ARN = "arn:aws:iam::514246413945:role/emr_s3_admin" # <--- IMPORTANT: Ensure this is NOT a Service-Linked Role for EMR Serverless Job Runs

# --- AWS Clients ---
s3_client = boto3.client('s3', region_name='ap-northeast-1')
emr_serverless_client = boto3.client('emr-serverless', region_name='ap-northeast-1')

def parse_s3_path(s3_path):
    parsed_url = urlparse(s3_path)
    bucket = parsed_url.netloc
    key = parsed_url.path.lstrip('/')
    return bucket, key

def check_s3_path(s3_path, is_file=True, check_write=False):
    bucket, key = parse_s3_path(s3_path)
    print(f"Checking S3 path: {s3_path} (Bucket: {bucket}, Key: {key})")
    try:
        if is_file:
            s3_client.head_object(Bucket=bucket, Key=key)
            print(f"  [OK] S3 file exists: {s3_path}")
        else: # It's a directory/prefix
            response = s3_client.list_objects_v2(Bucket=bucket, Prefix=key, MaxKeys=1)
            if 'Contents' in response and len(response['Contents']) > 0:
                print(f"  [OK] S3 directory/prefix exists and contains objects: {s3_path}")
            else:
                print(f"  [WARN] S3 directory/prefix exists but is empty: {s3_path}")
        
        if check_write:
            test_key = f"{key.rstrip('/')}/test_write_{uuid.uuid4()}.txt"
            s3_client.put_object(Bucket=bucket, Key=test_key, Body="test")
            s3_client.delete_object(Bucket=bucket, Key=test_key)
            print(f"  [OK] S3 write permission confirmed for: {s3_path}")
        return True
    except s3_client.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"  [ERROR] S3 path does not exist: {s3_path}")
        elif e.response['Error']['Code'] == '403':
            print(f"  [ERROR] S3 permission denied for: {s3_path}")
        else:
            print(f"  [ERROR] S3 error for {s3_path}: {e}")
        return False
    except Exception as e:
        print(f"  [ERROR] Unexpected error checking S3 path {s3_path}: {e}")
        return False

def check_emr_serverless_application(app_id):
    print(f"Checking EMR Serverless Application: {app_id}")
    try:
        response = emr_serverless_client.get_application(applicationId=app_id)
        app_state = response['application']['state']
        print(f"  [OK] EMR Serverless Application '{app_id}' exists and is in state: {app_state}")
        if app_state not in ['CREATED', 'STARTED', 'RUNNING']:
            print(f"  [WARN] Application is not in a ready state. Current state: {app_state}")
        return True
    except emr_serverless_client.exceptions.ResourceNotFoundException:
        print(f"  [ERROR] EMR Serverless Application '{app_id}' not found.")
        return False
    except Exception as e:
        print(f"  [ERROR] Error checking EMR Serverless Application '{app_id}': {e}")
        return False

def validate_emr_execution_role(app_id, role_arn):
    print(f"Validating EMR Execution Role: {role_arn} with Application: {app_id}")
    # Attempt to start a dummy job run to validate the role
    # This job will likely fail quickly if the role is invalid or permissions are missing
    try:
        dummy_job_name = f"test-role-{uuid.uuid4()}"
        response = emr_serverless_client.start_job_run(
            applicationId=app_id,
            clientToken=str(uuid.uuid4()),
            executionRoleArn=role_arn,
            jobDriver={
                'sparkSubmit': {
                    'entryPoint': 's3://us-east-1.elasticmapreduce/emr-containers/samples/wordcount/scripts/wordcount.py', # A public sample script
                    'entryPointArguments': ['s3://us-east-1.elasticmapreduce/emr-containers/samples/wordcount/input/wordcount', 's3://your-s3-bucket/output/'], # Dummy arguments
                    'sparkSubmitParameters': '--conf spark.executor.cores=1 --conf spark.executor.memory=1g'
                }
            },
            configurationOverrides={
                'monitoringConfiguration': {
                    's3MonitoringConfiguration': {'logUri': LOG_URI}
                }
            },
            name=dummy_job_name
        )
        job_run_id = response['jobRunId']
        print(f"  [OK] Successfully initiated a dummy job run with role. Job Run ID: {job_run_id}")
        print(f"  Please check AWS EMR Serverless console for job '{dummy_job_name}' ({job_run_id}) status.")
        print("  This dummy job will likely fail as it's not configured for your specific S3 paths,")
        print("  but its successful initiation indicates the role is valid for starting jobs.")
        return True
    except emr_serverless_client.exceptions.ValidationException as e:
        print(f"  [ERROR] Validation Error when starting dummy job: {e}")
        print("  This often indicates an issue with the executionRoleArn itself (e.g., Service-Linked Role, invalid format, or missing basic EMR Serverless permissions).")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error when starting dummy job: {e}")
        return False

def main():
    print("--- Starting AWS EMR Serverless Configuration Check ---")
    print("\n--- S3 Path Checks ---")
    s3_checks_passed = True
    s3_checks_passed &= check_s3_path(SPARK_SCRIPT_S3_PATH, is_file=True, check_write=False)
    s3_checks_passed &= check_s3_path(AI_INFERENCE_SCRIPT_S3_PATH, is_file=True, check_write=False)
    s3_checks_passed &= check_s3_path(INPUT_DATA_S3_PATH, is_file=False, check_write=False)
    s3_checks_passed &= check_s3_path(OUTPUT_DATA_S3_PATH, is_file=False, check_write=True)
    s3_checks_passed &= check_s3_path(INFERENCE_RESULTS_S3_PATH, is_file=False, check_write=True)
    s3_checks_passed &= check_s3_path(LOG_URI, is_file=False, check_write=True)

    print("\n--- EMR Serverless Application Check ---")
    app_check_passed = check_emr_serverless_application(EMR_SERVERLESS_APPLICATION_ID)

    print("\n--- EMR Execution Role Validation ---")
    role_validation_passed = False
    if app_check_passed: # Only attempt role validation if application exists
        role_validation_passed = validate_emr_execution_role(EMR_SERVERLESS_APPLICATION_ID, EMR_EXECUTION_ROLE_ARN)
    else:
        print("Skipping role validation as EMR Serverless Application was not found.")

    print("\n--- Summary ---")
    if s3_checks_passed and app_check_passed and role_validation_passed:
        print("[OK] All critical configuration checks passed. The issue might be within the PySpark script logic or more subtle AWS permissions.")
    else:
        print("❌ Some critical configuration checks failed. Please review the errors above and correct them.")

if __name__ == "__main__":
    main()
