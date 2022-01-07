import asyncio
import json
import os

import sentry_sdk

sentry_sdk.init(
    os.getenv("SENTRY_DSN", None),
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)

from main import app, analyze_orgchart, get_orgchart_image, cache_all_orgchart_images
from mangum import Mangum


@app.get("/", tags=["Endpoint Test"])
def main_endpoint_test():
    return {"message": "Just another strukturen API! [orgchart-ml]"}


SNS_ACTIONS_MAPPING = {
    "analyze-orgchart": analyze_orgchart,
    "orgchart-image": get_orgchart_image,
    "cache-all-orgchart-images": cache_all_orgchart_images,
}


def handler(event, context):
    if "requestContext" not in event:
        event["requestContext"] = {}

    # ugly glue-code to make serverless custom images combined with sns and magnum work for now
    if "Records" in event:
        # if there is a records list it should be always sns
        event = json.loads(event["Records"][0]["Sns"]["Message"])
        if event["action"] in SNS_ACTIONS_MAPPING:
            asyncio.run(SNS_ACTIONS_MAPPING[event["action"]](**event["parameters"]))
        return {"ok": True, "message": "SNS Task executed successfully"}
    # end of ugly glue code

    asgi_handler = Mangum(app)
    response = asgi_handler(
        event, context
    )  # Call the instance with the event arguments

    return response
