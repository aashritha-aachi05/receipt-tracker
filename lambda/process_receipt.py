import os
import boto3
import uuid
from datetime import datetime

textract = boto3.client("textract")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def handler(event, context):
    # Step 1: get bucket and file key from the S3 event
    record = event["Records"][0]
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]

    # Step 2: call Textract's analyze_document in forms mode
    response = textract.analyze_document(
        Document={"S3Object": {"Bucket": bucket, "Name": key}},
        FeatureTypes=["FORMS"],
    )

    # Step 3: parse key-value pairs out of Textract's response
    vendor, total = extract_vendor_and_total(response)

    # Step 4: write the clean record to DynamoDB
    table.put_item(
        Item={
            "receiptId": str(uuid.uuid4()),
            "vendor": vendor or "UNKNOWN",
            "total": total or "UNKNOWN",
            "uploadedAt": datetime.utcnow().isoformat(),
            "sourceFile": key,
        }
    )

    return {"statusCode": 200, "body": "Receipt processed"}


def extract_vendor_and_total(textract_response):
    """Walk Textract's FORMS output looking for key-value pairs we care about."""
    blocks = textract_response["Blocks"]
    key_map = {}
    value_map = {}
    block_map = {}

    for block in blocks:
        block_id = block["Id"]
        block_map[block_id] = block
        if block["BlockType"] == "KEY_VALUE_SET":
            if "KEY" in block.get("EntityTypes", []):
                key_map[block_id] = block
            else:
                value_map[block_id] = block

    vendor = None
    total = None

    for key_block in key_map.values():
        key_text = _get_text(key_block, block_map).strip().lower()
        value_block = _get_value_block(key_block, block_map)
        value_text = _get_text(value_block, block_map).strip() if value_block else ""

        if "total" in key_text and total is None:
            total = value_text
        if ("vendor" in key_text or "merchant" in key_text or "store" in key_text) and vendor is None:
            vendor = value_text

    return vendor, total


def _get_text(block, block_map):
    text = ""
    for relationship in block.get("Relationships", []):
        if relationship["Type"] == "CHILD":
            for child_id in relationship["Ids"]:
                child = block_map.get(child_id)
                if child and child["BlockType"] == "WORD":
                    text += child["Text"] + " "
    return text


def _get_value_block(key_block, block_map):
    for relationship in key_block.get("Relationships", []):
        if relationship["Type"] == "VALUE":
            for value_id in relationship["Ids"]:
                return block_map.get(value_id)
    return None