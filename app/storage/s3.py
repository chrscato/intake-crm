import boto3, uuid, json
from app.settings import settings
s3 = boto3.client('s3',
                  aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                  region_name=settings.AWS_REGION)

def upload_raw(msg: dict):
    key = f"raw/{uuid.uuid4()}.json"
    s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=json.dumps(msg).encode())
    return key
