"""
AWS S3 Integration Nodes - Upload, download, and manage S3 objects.
"""

import asyncio
from pathlib import Path

from src.core.nodes.base import BaseNode, FieldType, NodeField


class S3UploadNode(BaseNode):
    """
    Upload files to AWS S3.
    """

    type = "s3-upload"
    name = "AWS S3: Upload"
    category = "Apps"
    description = "Upload a file to S3 bucket"
    icon = "cloud_upload"
    color = "#FF9900"  # AWS orange

    inputs = [
        NodeField(
            name="access_key",
            label="Access Key ID",
            type=FieldType.SECRET,
            required=True,
            description="AWS Access Key ID.",
        ),
        NodeField(
            name="secret_key",
            label="Secret Access Key",
            type=FieldType.SECRET,
            required=True,
            description="AWS Secret Access Key.",
        ),
        NodeField(
            name="region",
            label="Region",
            type=FieldType.STRING,
            required=False,
            default="us-east-1",
            description="AWS region.",
        ),
        NodeField(
            name="bucket",
            label="Bucket Name",
            type=FieldType.STRING,
            required=True,
        ),
        NodeField(
            name="key",
            label="Object Key",
            type=FieldType.STRING,
            required=True,
            description="S3 object key (path in bucket).",
        ),
        NodeField(
            name="file_path",
            label="Local File Path",
            type=FieldType.STRING,
            required=False,
            description="Path to local file to upload.",
        ),
        NodeField(
            name="content",
            label="Content",
            type=FieldType.TEXT,
            required=False,
            description="Text content to upload (if no file path).",
        ),
        NodeField(
            name="content_type",
            label="Content Type",
            type=FieldType.STRING,
            required=False,
            default="application/octet-stream",
        ),
        NodeField(
            name="acl",
            label="ACL",
            type=FieldType.SELECT,
            required=False,
            default="private",
            options=[
                {"value": "private", "label": "Private"},
                {"value": "public-read", "label": "Public Read"},
                {"value": "public-read-write", "label": "Public Read/Write"},
            ],
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
        ),
        NodeField(
            name="url",
            label="Object URL",
            type=FieldType.STRING,
        ),
        NodeField(
            name="etag",
            label="ETag",
            type=FieldType.STRING,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Upload to S3."""
        try:
            import boto3
        except ImportError:
            raise RuntimeError("boto3 not installed. Install with: pip install boto3")

        access_key = config.get("access_key", "")
        secret_key = config.get("secret_key", "")
        region = config.get("region", "us-east-1")
        bucket = config.get("bucket", "")
        key = config.get("key", "")
        file_path = config.get("file_path")
        content = config.get("content")
        content_type = config.get("content_type", "application/octet-stream")
        acl = config.get("acl", "private")

        loop = asyncio.get_event_loop()

        def upload():
            s3 = boto3.client(
                "s3",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
            )

            extra_args = {"ContentType": content_type, "ACL": acl}

            if file_path:
                s3.upload_file(file_path, bucket, key, ExtraArgs=extra_args)
            elif content:
                s3.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=content.encode() if isinstance(content, str) else content,
                    **extra_args,
                )
            else:
                raise ValueError("Either file_path or content is required")

            # Get object info
            head = s3.head_object(Bucket=bucket, Key=key)

            url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
            return {
                "success": True,
                "url": url,
                "etag": head.get("ETag", "").strip('"'),
            }

        try:
            result = await loop.run_in_executor(None, upload)
            return result
        except Exception:
            return {
                "success": False,
                "url": "",
                "etag": "",
            }


class S3DownloadNode(BaseNode):
    """
    Download files from AWS S3.
    """

    type = "s3-download"
    name = "AWS S3: Download"
    category = "Apps"
    description = "Download a file from S3 bucket"
    icon = "cloud_download"
    color = "#FF9900"

    inputs = [
        NodeField(
            name="access_key",
            label="Access Key ID",
            type=FieldType.SECRET,
            required=True,
        ),
        NodeField(
            name="secret_key",
            label="Secret Access Key",
            type=FieldType.SECRET,
            required=True,
        ),
        NodeField(
            name="region",
            label="Region",
            type=FieldType.STRING,
            required=False,
            default="us-east-1",
        ),
        NodeField(
            name="bucket",
            label="Bucket Name",
            type=FieldType.STRING,
            required=True,
        ),
        NodeField(
            name="key",
            label="Object Key",
            type=FieldType.STRING,
            required=True,
        ),
        NodeField(
            name="file_path",
            label="Save to Path",
            type=FieldType.STRING,
            required=False,
            description="Local path to save file (optional).",
        ),
    ]

    outputs = [
        NodeField(
            name="success",
            label="Success",
            type=FieldType.BOOLEAN,
        ),
        NodeField(
            name="content",
            label="Content",
            type=FieldType.STRING,
            description="File content (if text).",
        ),
        NodeField(
            name="size",
            label="Size (bytes)",
            type=FieldType.NUMBER,
        ),
        NodeField(
            name="file_path",
            label="Saved Path",
            type=FieldType.STRING,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """Download from S3."""
        try:
            import boto3
        except ImportError:
            raise RuntimeError("boto3 not installed. Install with: pip install boto3")

        access_key = config.get("access_key", "")
        secret_key = config.get("secret_key", "")
        region = config.get("region", "us-east-1")
        bucket = config.get("bucket", "")
        key = config.get("key", "")
        file_path = config.get("file_path")

        loop = asyncio.get_event_loop()

        def download():
            s3 = boto3.client(
                "s3",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
            )

            if file_path:
                s3.download_file(bucket, key, file_path)
                size = Path(file_path).stat().st_size
                return {
                    "success": True,
                    "content": "",
                    "size": size,
                    "file_path": file_path,
                }
            else:
                response = s3.get_object(Bucket=bucket, Key=key)
                body = response["Body"].read()
                try:
                    content = body.decode("utf-8")
                except:
                    content = f"[Binary data: {len(body)} bytes]"
                return {
                    "success": True,
                    "content": content,
                    "size": len(body),
                    "file_path": "",
                }

        try:
            result = await loop.run_in_executor(None, download)
            return result
        except Exception:
            return {
                "success": False,
                "content": "",
                "size": 0,
                "file_path": "",
            }


class S3ListObjectsNode(BaseNode):
    """
    List objects in an S3 bucket.
    """

    type = "s3-list-objects"
    name = "AWS S3: List Objects"
    category = "Apps"
    description = "List objects in an S3 bucket"
    icon = "folder_open"
    color = "#FF9900"

    inputs = [
        NodeField(
            name="access_key",
            label="Access Key ID",
            type=FieldType.SECRET,
            required=True,
        ),
        NodeField(
            name="secret_key",
            label="Secret Access Key",
            type=FieldType.SECRET,
            required=True,
        ),
        NodeField(
            name="region",
            label="Region",
            type=FieldType.STRING,
            required=False,
            default="us-east-1",
        ),
        NodeField(
            name="bucket",
            label="Bucket Name",
            type=FieldType.STRING,
            required=True,
        ),
        NodeField(
            name="prefix",
            label="Prefix",
            type=FieldType.STRING,
            required=False,
            description="Filter by key prefix (folder path).",
        ),
        NodeField(
            name="max_keys",
            label="Max Keys",
            type=FieldType.NUMBER,
            required=False,
            default=1000,
        ),
    ]

    outputs = [
        NodeField(
            name="objects",
            label="Objects",
            type=FieldType.JSON,
        ),
        NodeField(
            name="count",
            label="Count",
            type=FieldType.NUMBER,
        ),
    ]

    async def execute(self, config: dict, context: dict) -> dict:
        """List S3 objects."""
        try:
            import boto3
        except ImportError:
            raise RuntimeError("boto3 not installed. Install with: pip install boto3")

        access_key = config.get("access_key", "")
        secret_key = config.get("secret_key", "")
        region = config.get("region", "us-east-1")
        bucket = config.get("bucket", "")
        prefix = config.get("prefix", "")
        max_keys = int(config.get("max_keys", 1000))

        loop = asyncio.get_event_loop()

        def list_objects():
            s3 = boto3.client(
                "s3",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
            )

            params = {"Bucket": bucket, "MaxKeys": max_keys}
            if prefix:
                params["Prefix"] = prefix

            response = s3.list_objects_v2(**params)

            objects = []
            for obj in response.get("Contents", []):
                objects.append(
                    {
                        "key": obj.get("Key"),
                        "size": obj.get("Size"),
                        "last_modified": obj.get("LastModified").isoformat()
                        if obj.get("LastModified")
                        else None,
                        "etag": obj.get("ETag", "").strip('"'),
                    }
                )

            return objects

        try:
            objects = await loop.run_in_executor(None, list_objects)
            return {
                "objects": objects,
                "count": len(objects),
            }
        except Exception:
            return {
                "objects": [],
                "count": 0,
            }
