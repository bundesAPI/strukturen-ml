import io

import boto3


class S3Cache:
    def __init__(self, bucket):
        self.s3_resource = boto3.resource("s3")
        self.s3_client = boto3.client("s3")
        self.bucket = bucket

    def get_item(self, key: str):
        try:
            response = self.s3_resource.Object(self.bucket, key + ".png").get()
        except self.s3_client.exceptions.NoSuchKey:
            return None
        buf = io.BytesIO()
        buf.write(response["Body"].read())
        buf.seek(0)
        return buf

    def set_item(self, key: str, file_):
        print(key + ".png")
        self.s3_client.put_object(Body=file_, Bucket=self.bucket, Key=key + ".png")
