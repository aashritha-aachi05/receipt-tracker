import aws_cdk as core
import aws_cdk.assertions as assertions

from receipt_tracker.receipt_tracker_stack import ReceiptTrackerStack

# example tests. To run these tests, uncomment this file along with the example
# resource in receipt_tracker/receipt_tracker_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ReceiptTrackerStack(app, "receipt-tracker")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
