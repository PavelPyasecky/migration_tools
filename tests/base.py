from unittest import TestCase, mock

from sqlalchemy import create_engine

import settings
from db.models import mapper_registry
from services.file_uploader import FileUploader

test_engine = create_engine(settings.TEST_DB_CONNECTION_STRING, echo=True)


class AppTestCase(TestCase):
    def setUp(self):
        mapper_registry.metadata.create_all(test_engine)

        self.upload_file_mock = self.create_patch(
            'services.file_uploader.FileUploader.upload_file',
        )

        self.upload_file_from_path_mock = self.create_patch(
            'services.file_uploader.FileUploader.upload_file',
            side_effect=upload_file_from_path_mock_side_effect
        )

    def tearDown(self):
        mapper_registry.metadata.drop_all(test_engine)

    def start_patch(self, patcher):
        mock_instance = patcher.start()
        self.addCleanup(patcher.stop)
        return mock_instance

    def create_patch(self, path, **kwargs):
        patcher = mock.patch(path, **kwargs)
        return self.start_patch(patcher)


def upload_file_from_path_mock_side_effect(self, file_path):
    return FileUploader.get_file_name_by_path(file_path)
