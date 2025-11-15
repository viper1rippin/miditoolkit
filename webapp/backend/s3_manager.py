"""
AWS S3 Manager for file uploads
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import os
from pathlib import Path


class S3Manager:
    """Manager for AWS S3 operations."""

    def __init__(self):
        """Initialize S3 manager."""
        self.s3_client = None
        self.bucket_name = None
        self.region_name = None
        self._configured = False

        # Try to load from environment variables
        self._load_from_env()

    def _load_from_env(self):
        """Load S3 configuration from environment variables."""
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        region_name = os.getenv('AWS_REGION', 'us-east-1')
        bucket_name = os.getenv('S3_BUCKET_NAME')

        if aws_access_key_id and aws_secret_access_key and bucket_name:
            self.configure(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name,
                bucket_name=bucket_name
            )

    def configure(self, aws_access_key_id, aws_secret_access_key, region_name, bucket_name):
        """
        Configure S3 client with credentials.

        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region_name: AWS region (e.g., 'us-east-1')
            bucket_name: S3 bucket name
        """
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name
            )

            self.bucket_name = bucket_name
            self.region_name = region_name
            self._configured = True

            # Save to environment (for this session)
            os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key_id
            os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_access_key
            os.environ['AWS_REGION'] = region_name
            os.environ['S3_BUCKET_NAME'] = bucket_name

        except Exception as e:
            self._configured = False
            raise Exception(f"Failed to configure S3: {str(e)}")

    def is_configured(self):
        """Check if S3 is configured."""
        return self._configured and self.s3_client is not None

    def test_connection(self):
        """
        Test S3 connection by listing buckets.

        Returns:
            bool: True if connection is successful
        """
        if not self.is_configured():
            return False

        try:
            # Try to head the bucket
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            return False
        except NoCredentialsError:
            return False
        except Exception:
            return False

    def upload_file(self, file_path, s3_key=None, metadata=None):
        """
        Upload a file to S3.

        Args:
            file_path: Local file path to upload
            s3_key: S3 object key (path in bucket). If None, uses filename
            metadata: Optional metadata dictionary

        Returns:
            str: S3 key of uploaded file

        Raises:
            Exception: If upload fails
        """
        if not self.is_configured():
            raise Exception("S3 not configured")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Generate S3 key if not provided
        if s3_key is None:
            s3_key = Path(file_path).name

        try:
            # Prepare upload arguments
            extra_args = {}

            if metadata:
                extra_args['Metadata'] = metadata

            # Determine content type
            if file_path.endswith('.json'):
                extra_args['ContentType'] = 'application/json'
            elif file_path.endswith('.mid') or file_path.endswith('.midi'):
                extra_args['ContentType'] = 'audio/midi'

            # Upload file
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args if extra_args else None
            )

            return s3_key

        except ClientError as e:
            raise Exception(f"S3 upload failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Upload failed: {str(e)}")

    def download_file(self, s3_key, local_path):
        """
        Download a file from S3.

        Args:
            s3_key: S3 object key
            local_path: Local path to save file

        Raises:
            Exception: If download fails
        """
        if not self.is_configured():
            raise Exception("S3 not configured")

        try:
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                local_path
            )
        except ClientError as e:
            raise Exception(f"S3 download failed: {str(e)}")

    def delete_file(self, s3_key):
        """
        Delete a file from S3.

        Args:
            s3_key: S3 object key to delete

        Raises:
            Exception: If deletion fails
        """
        if not self.is_configured():
            raise Exception("S3 not configured")

        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
        except ClientError as e:
            raise Exception(f"S3 deletion failed: {str(e)}")

    def list_files(self, prefix=''):
        """
        List files in S3 bucket.

        Args:
            prefix: Optional prefix to filter files

        Returns:
            list: List of S3 object keys

        Raises:
            Exception: If listing fails
        """
        if not self.is_configured():
            raise Exception("S3 not configured")

        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            if 'Contents' not in response:
                return []

            return [obj['Key'] for obj in response['Contents']]

        except ClientError as e:
            raise Exception(f"S3 listing failed: {str(e)}")

    def get_file_url(self, s3_key, expiration=3600):
        """
        Generate a presigned URL for file access.

        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            str: Presigned URL

        Raises:
            Exception: If URL generation fails
        """
        if not self.is_configured():
            raise Exception("S3 not configured")

        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f"URL generation failed: {str(e)}")
