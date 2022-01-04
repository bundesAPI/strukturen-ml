import json

import boto3


def generate_image_sns(queue_arn, orgchart_id, page, position=[]):
    client = boto3.client("sns")
    message = {
        "action": "orgchart-image",
        "parameters": {"orgchart_id": orgchart_id, "page": page, "position": position},
    }
    response = client.publish(TopicArn=queue_arn, Message=json.dumps(message))
    return response
