import boto3
import os



# Get bucket name from environment or hardcode
S3_BUCKET = os.getenv("S3_BUCKET", "documentportal-storage")
print(boto3.session.Session().get_credentials())

s3 = boto3.client("s3")

def upload_to_s3(local_path: str, s3_key: str):
    try:
        s3.upload_file(local_path, S3_BUCKET, s3_key)
        return f"s3://{S3_BUCKET}/{s3_key}"
    except Exception as e:
        raise RuntimeError(f"Failed to upload {local_path} -> {s3_key}: {str(e)}")
