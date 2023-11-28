import os

FILE_UPLOAD_BUCKET_NAME = 'chashaby'
AWS_S3_URL = 'https://{bucket_name}.s3.eu-central-1.amazonaws.com/{file_name}'

AWS_REGION = 'eu-central-1'

AWS_S3_ACCESS_KEY_ID = os.getenv('AWS_S3_ACCESS_KEY_ID')
AWS_S3_ACCESS_SECRET_KEY = os.getenv('AWS_S3_ACCESS_SECRET_KEY')

ASSET_MANAGER_S3 = {
    'key': AWS_S3_ACCESS_KEY_ID,
    'secret': AWS_S3_ACCESS_SECRET_KEY,
}

TEST_DB_CONNECTION_STRING = 'sqlite://'
PROD_DB_CONNECTION_STRING = os.getenv('DB_CONNECTION_STRING')
