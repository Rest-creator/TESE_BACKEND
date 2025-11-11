import os
import uuid
import boto3
from botocore.exceptions import NoCredentialsError, ClientError


try:
    AWS_S3_BUCKET_NAME = os.environ.get("AWS_S3_BUCKET_NAME")
    AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")

    if not AWS_S3_BUCKET_NAME or not AWS_DEFAULT_REGION:
        raise ValueError("AWS_S3_BUCKET_NAME or AWS_DEFAULT_REGION env vars not set.")

    s3_client = boto3.client('s3', region_name=AWS_DEFAULT_REGION)

except (NoCredentialsError, ValueError) as e:
    print(f"Error initializing S3 client: {e}")
    s3_client = None


class S3Client:

    @staticmethod
    def upload_file(file_name: str, file_content: bytes, content_type: str) -> str:
        """
        Uploads a file to AWS S3 and returns its public URL.
        """
        if not s3_client:
            raise ConnectionError("S3 client not initialized.")

        # Create a unique filename
        unique_filename = f"{uuid.uuid4()}-{file_name}"

        try:
            # Upload the file
            s3_client.put_object(
                Bucket=AWS_S3_BUCKET_NAME,
                Key=unique_filename,
                Body=file_content,
                ContentType=content_type,
                ACL='public-read'  # This makes the *specific file* public
            )

            public_url = f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_DEFAULT_REGION}.amazonaws.com/{unique_filename}"
            return public_url

        except ClientError as e:
            print(f"AWS S3 upload failed: {e}")
            raise e
        except Exception as e:
            print(f"An unexpected error occurred during S3 upload: {e}")
            raise e