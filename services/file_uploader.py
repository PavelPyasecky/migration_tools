import logging
from abc import ABC
from typing import Optional, Dict
from urllib.parse import unquote

import boto3
import magic
from requests import Timeout, ConnectTimeout

import settings

from botocore.exceptions import ClientError
from io import BytesIO

from utils import stored_property


logger = logging.getLogger(__name__)


class ObjectKeyNotFound(Exception):
    pass


class FileUploadError(Exception):
    pass


def create_default_aws_session(credentials: Optional[Dict[str, str]] =
                               settings.ASSET_MANAGER_S3) -> boto3.session.Session:
    return boto3.session.Session(
        region_name=settings.AWS_REGION,
        aws_access_key_id=credentials['key'],
        aws_secret_access_key=credentials['secret']
    )


def create_default_s3_aws_session() -> boto3.session.Session:
    return create_default_aws_session()


class AWSSessionCreator:

    SERVICE_NAME_TO_SESSION_CREATOR_MAPPING = {
        's3': create_default_s3_aws_session,
    }

    def create_aws_session_for_service(self, service_name: str) -> boto3.session.Session:
        session_creator = self.SERVICE_NAME_TO_SESSION_CREATOR_MAPPING[service_name]
        return session_creator()


class AWSClient(ABC):
    """
    A class to extend for communicating with an AWS service in our AWS account.
    """
    service_name: str = NotImplementedError

    def __init__(self, session: Optional[boto3.session.Session] = None):
        self.aws_session = session or AWSSessionCreator().create_aws_session_for_service(self.service_name)

    @stored_property
    def service_client(self):
        return self.aws_session.client(self.service_name)


class AWSClientWithResource(AWSClient):
    """
    Some AWS services are exposed by boto3 with only 'boto3.client()' functionality; others make use of
    additional classes as well. This class is for AWSClient subclasses utilizing an AWS service that also
    has 'boto3.resource()' functionality.
    """
    service_name: str = NotImplementedError

    @stored_property
    def service_resource(self):
        return self.aws_session.resource(self.service_name)


class S3Client(AWSClientWithResource):
    service_name = 's3'

    def _get_bucket(self, bucket_name):
        return self.service_resource.Bucket(bucket_name)

    def _get_object(self, bucket_name, key):
        return self.service_resource.Object(bucket_name, key)

    def get_objects(self, bucket_name, key_prefix):
        bucket = self._get_bucket(bucket_name)
        s3_items = bucket.objects.filter(Prefix=key_prefix)
        return [s3_item.key for s3_item in s3_items]

    def upload_body_data(self, bucket_name, key, body, **kwargs):
        bucket = self._get_bucket(bucket_name)
        return bucket.put_object(Key=key, Body=body, **kwargs)

    def delete_objects(self, bucket_name, keys_to_delete):
        objects_to_delete = [{'Key': key} for key in keys_to_delete]
        bucket = self._get_bucket(bucket_name)
        bucket.delete_objects(Delete={'Objects': objects_to_delete})

    def copy_object(self, src_bucket, src_key, dest_bucket, dest_key):
        self.service_client.copy_object(
            Bucket=dest_bucket,
            Key=dest_key,
            CopySource='%s/%s' % (src_bucket, src_key),
        )

    def get_file_body(self, bucket_name, key):
        obj = self._get_object(bucket_name, key)
        try:
            data = obj.get()
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'NoSuchKey':
                raise ObjectKeyNotFound('Key %s was not found.' % key)
            raise ex
        return data['Body'], data['ContentType']

    def download_file_bytes_to_stream(self, bucket_name, file_name):
        file_data = BytesIO()
        self._get_bucket(bucket_name).download_fileobj(Key=file_name, Fileobj=file_data)

        return file_data


class FileUploadBase:

    def __init__(self):
        self._s3_client = S3Client()

    @property
    def bucket_name(self):
        return settings.FILE_UPLOAD_BUCKET_NAME


class FileUploadProcessor(FileUploadBase):

    def upload_file(self, key, fileobj, **kwargs):
        kwargs.update(self._set_content_type_if_needed(fileobj))
        return self._s3_client.upload_body_data(self.bucket_name, key, fileobj, **kwargs)

    def _set_content_type_if_needed(self, fileobj) -> dict:
        mime_service = magic.Magic(mime=True, uncompress=True)
        mimetype = mime_service.from_buffer(fileobj.read(2048))
        fileobj.seek(0)

        if mimetype.startswith('image'):
            return {'ContentType': mimetype}

        return {}


class FileUploader:
    def upload_file(self, fileobj, key):
        file_upload_processor = FileUploadProcessor()
        return file_upload_processor.upload_file(key, fileobj)

    def upload_file_from_path(self, file_path) -> str:
        file_name = self.get_file_name_by_path(file_path)

        try:
            with open(file_path, "rb") as fileobj:
                self.upload_file(fileobj, file_name)
                return file_name

        except (Timeout, ConnectTimeout, ConnectionError) as e:
            logger.error(f'Upload file error: {e}')
            return ''

        except FileNotFoundError as e:
            logger.error(f'File is not found: {e}')
            return ''

    @staticmethod
    def get_file_name_by_path(path):
        return unquote(path.split('/')[-1])
