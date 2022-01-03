import os

import sentry_sdk

sentry_sdk.init(
    os.getenv("SENTRY_DSN", None),
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)

from main import app
from mangum import Mangum


@app.get("/", tags=["Endpoint Test"])
def main_endpoint_test():
    return {"message": "Just another strukturen API! [orgchart-ml]"}


def handler(event, context):
    print(event)
    print(context)
    if "requestContext" not in event:
        event["requestContext"] = {}

    asgi_handler = Mangum(app)
    response = asgi_handler(
        event, context
    )  # Call the instance with the event arguments

    return response
