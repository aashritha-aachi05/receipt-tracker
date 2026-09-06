# Serverless Receipt Tracker

A small AWS pipeline that turns a photo of a receipt into a structured database record. Upload a receipt image to S3, and within seconds you get a clean entry in DynamoDB with the vendor name and total pulled out automatically.

## How it works

1. You drop a receipt image into an S3 bucket.
2. That upload triggers a Lambda function automatically (no polling, no manual invocation).
3. The Lambda sends the image to Amazon Textract using its forms analysis mode, which detects label/value pairs on the page instead of just returning a wall of raw text.
4. The Lambda walks through Textract's response looking for anything that looks like "Total" or "Vendor," pulls out the matching values, and writes a record to DynamoDB.

```
S3 (upload) -> Lambda -> Textract (AnalyzeDocument, FORMS) -> DynamoDB
```

The whole thing is defined as infrastructure-as-code using AWS CDK (Python), so the entire stack can be deployed or torn down with one command.

## Why these choices

**Textract's forms mode over basic text detection.** Basic OCR just gives you a flat list of text lines with no structure, which means you'd need to write fragile regex or heuristics to guess which line is the total. Forms mode tries to detect key-value pairs on the page itself, so parsing is a matter of scanning for a key containing "total" rather than pattern-matching raw text. The tradeoff is cost (forms analysis is priced higher than plain text detection) and the fact that it doesn't work perfectly on every receipt layout - some receipts don't get cleanly detected as key-value pairs, and the parser falls back to "UNKNOWN" in those cases rather than guessing wrong.

**DynamoDB over a relational database.** Every read here is a simple lookup by receipt ID with no joins and no complex queries. DynamoDB is built for exactly that kind of access pattern and scales without any of the schema or query-tuning overhead a SQL database would add for a use case this simple.

**Environment variables instead of hardcoded resource names.** The Lambda doesn't know the DynamoDB table's name at write time - CDK injects it at deploy time as an environment variable. If the table gets renamed or redeployed, the Lambda picks up the new name automatically instead of needing a manual code change in two places.

**Broad IAM permissions during development, but not what I'd ship.** The CDK deploy user currently has AdministratorAccess, which is fine for a personal learning account but is not what this would look like in a real environment. A production version would scope the Lambda's role down to exactly what it needs: read from this one S3 bucket, write to this one DynamoDB table, call Textract's AnalyzeDocument action - nothing broader.

## What's not handled yet

- Receipts that don't cleanly form key-value pairs in Textract just get logged as "UNKNOWN" rather than falling back to a raw-text regex search.
- No retry or dead-letter handling if Textract or DynamoDB briefly fails.
- No automated tests beyond the CDK stack's default snapshot test.

These are the natural next steps if I keep building this out.

## Stack

Python, AWS CDK, S3, Lambda, Amazon Textract, DynamoDB

## Deploying this yourself

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cdk bootstrap
cdk deploy
```

After deploying, upload any receipt image to the created S3 bucket and check the DynamoDB table for the parsed result.
