import base64
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import uuid
import boto3

from parsers import extract_to_markdown

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET = os.getenv("S3_BUCKET", "doc-markdown-poc-mumbai")
DDB_TABLE = os.getenv("DDB_TABLE", "DocMarkdownMetadataPoc")

s3_client = boto3.client("s3", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(DDB_TABLE)


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    try:
        raw_body = event.get("body") if isinstance(event, dict) else event
        if isinstance(raw_body, str):
            payload = json.loads(raw_body or "{}")
        elif isinstance(raw_body, dict):
            payload = raw_body
        else:
            return _response(400, {"error": "Invalid request payload"})

        file_name = Path(payload.get("file_name") or "uploaded_file").name
        requested_parser = payload.get("parser") or "markitdown"
        file_b64 = payload.get("file_base64")

        if not file_b64:
            return _response(400, {"error": "Missing file_base64 content"})

        file_bytes = base64.b64decode(file_b64)
        file_size = len(file_bytes)

        if file_size == 0 or file_size >= MAX_FILE_SIZE_BYTES:
            return _response(400, {"error": "File size must be greater than 0 and strictly under 5 MB"})

        document_id = payload.get("document_id") or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        reference_s3_key = f"uploads/{document_id}/{file_name}"
        output_stem = Path(file_name).stem or "output"
        output_s3_key = f"outputs/{document_id}/{output_stem}.md"

        # 1. Save uploaded reference file to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=reference_s3_key,
            Body=file_bytes,
        )

        # 2. Write temp file in /tmp and extract to Markdown
        suffix = Path(file_name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir="/tmp") as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name

        try:
            parser_used, markdown_text = extract_to_markdown(tmp_path, requested_parser)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        # 3. Save converted Markdown output to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=output_s3_key,
            Body=markdown_text.encode("utf-8"),
            ContentType="text/markdown; charset=utf-8",
        )

        # 4. Save metadata in DynamoDB
        table.put_item(
            Item={
                "document_id": document_id,
                "file_name": file_name,
                "file_size": file_size,
                "parser_used": parser_used,
                "reference_s3_key": reference_s3_key,
                "output_s3_key": output_s3_key,
                "status": "COMPLETED",
                "created_at": created_at,
            }
        )

        return _response(
            200,
            {
                "document_id": document_id,
                "file_name": file_name,
                "file_size": file_size,
                "parser_used": parser_used,
                "reference_s3_key": reference_s3_key,
                "output_s3_key": output_s3_key,
                "markdown": markdown_text,
            },
        )

    except Exception as exc:
        return _response(500, {"error": f"Extraction failed: {str(exc)}"})