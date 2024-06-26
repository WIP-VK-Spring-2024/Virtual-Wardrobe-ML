"""Amazon S3 service."""
import pathlib
from typing import BinaryIO, Tuple
from io import BytesIO

import boto3
from botocore.exceptions import ClientError

from app.pkg.models.exceptions.amazon_s3 import AmazonS3NotFoundError, AmazonS3UploadError
from app.pkg.settings import settings
from app.pkg.logger import get_logger

__all__ = ["AmazonS3Service"]

logger = get_logger(__name__)

class AmazonS3Service:

    def __init__(self) -> None:
        self.s3 = boto3.client(
            service_name="s3",
            aws_access_key_id=settings.AWS.ACCESS_KEY_ID.get_secret_value(),
            aws_secret_access_key=settings.AWS.SECRET_ACCESS_KEY.get_secret_value(),
            endpoint_url=settings.AWS.ENDPOINT_URL,
        )
        self.s3_bucket_name = settings.AWS.BUCKET_NAME

    def get_file_path(self, file_name: str, folder: str = None) -> str:
        file_path = f"{folder}/{file_name}" if folder else file_name
        return file_path

    def upload(self, file: BinaryIO, file_name: str, folder: str = None) -> None:
        file_path = self.get_file_path(file_name, folder)
        extra_args = {'ACL': 'public-read'}
        try:
            res = self.s3.upload_fileobj(file, self.s3_bucket_name, file_path, ExtraArgs=extra_args)
            logger.info("Uploaded file to S3, response: %s", res)
        except ClientError as e:
            logger.error("Error for file path: %s, error: %s", file_path, e)
            raise AmazonS3UploadError from e
        
    def delete(self, file_name: str, folder: str = None) -> None:
        file_path = self.get_file_path(file_name, folder)
        try:
            res = self.s3.delete_object(Bucket=self.s3_bucket_name, Key=file_path)
            logger.info("Deleted file from S3, response: %s", res)
        except ClientError as e:
            logger.error("Error for file path: %s, error: %s", file_path, e)
            raise AmazonS3NotFoundError from e
        
    def read(self, file_name: str, folder: str = None) -> BinaryIO:
        file_path = self.get_file_path(file_name, folder)
        try:
            response = self.s3.get_object(Bucket=self.s3_bucket_name, Key=file_path)
            file_content = response["Body"].read()
            buffer = BytesIO(file_content)
            return buffer
        except ClientError as e:
            logger.error("Error for file path: %s, error: %s", file_path, e)
            raise AmazonS3NotFoundError from e


    def read_and_save(self, file_name: str, folder: str = None) -> Tuple[BinaryIO, str]:
        default_path = pathlib.Path(
            settings.API_FILESYSTEM_FOLDER,
            folder,
        ).absolute()
        if not default_path.exists():
            default_path.mkdir(exist_ok=True, parents=True)
        
        file_path = pathlib.Path(default_path, str(file_name)).absolute()

        contents = self.read(file_name=file_name, folder=folder)

        with open(file_path, 'wb') as f:
            f.write(contents.read())

        contents.seek(0)

        return contents, str(file_path)
