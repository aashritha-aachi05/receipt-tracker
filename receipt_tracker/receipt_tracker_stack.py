from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_s3_notifications as s3n,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
)
from constructs import Construct

class ReceiptTrackerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. The S3 bucket for receipt uploads
        receipt_bucket = s3.Bucket(
            self, "ReceiptBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # 2. The DynamoDB table for storing parsed receipt data
        receipts_table = dynamodb.Table(
            self, "ReceiptsTable",
            partition_key=dynamodb.Attribute(
                name="receiptId",
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )

        # 3. The Lambda function that processes uploads
        process_lambda = _lambda.Function(
            self, "ProcessReceiptFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="process_receipt.handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            environment={
                "TABLE_NAME": receipts_table.table_name
            },
        )

        # 4. Grant the Lambda permission to write to the table
        receipts_table.grant_write_data(process_lambda)

        # 5. Grant the Lambda permission to read from the S3 bucket and call Textract
        receipt_bucket.grant_read(process_lambda)
        process_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["textract:AnalyzeDocument"],
                resources=["*"],
            )
        )

        # 6. Wire the bucket to trigger the Lambda on upload
        receipt_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(process_lambda),
        )