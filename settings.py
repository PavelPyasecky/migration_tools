import os

FILE_UPLOAD_BUCKET_NAME = 'chashaby'

AWS_REGION = 'eu-central-1'

AWS_S3_ACCESS_KEY_ID = os.getenv('AWS_S3_ACCESS_KEY_ID')
AWS_S3_ACCESS_SECRET_KEY = os.getenv('AWS_S3_ACCESS_SECRET_KEY')

ASSET_MANAGER_S3 = {
    'key': AWS_S3_ACCESS_KEY_ID,
    'secret': AWS_S3_ACCESS_SECRET_KEY,
}

DB_CONNECTION_STRING = os.getenv('DB_CONNECTION_STRING')
