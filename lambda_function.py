import sentry_sdk
sentry_sdk.init(
    "https://34f8c1e12f5b4db685e53599776be4c9@o1094272.ingest.sentry.io/6130501",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0
)

from main import app
from mangum import Mangum


@app.get("/",  tags=["Endpoint Test"])
def main_endpoint_test():
    return {"message": "Just another strukturen API! [orgchart-ml]"}

handler = Mangum(app)