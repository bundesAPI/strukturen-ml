# Strukturen-ML
This service can be used via a restful api (synchronously) and via an SNS-Topic asynchronously.

[API Documentation](https://ml.beta.strukturen.bund.dev/docs/).

## Supported SNS Messages
Every method works the same way with the same GET-Parameters as documented in the API Documentation.

### Generate and cache images of an Orgchart.
**Topic:** ```orgchart-image-generator-ml-bund-dev```
```json
{
    "action": "orgchart-image",
    "parameters": {
        "orgchart_id": "T3JnQ2hhcnROb2RlOjQ=",
        "page": 0,
        "position": [78, 590, 131, 645]
    }
}
```

### Parse Orgchart
**Topic:** ```orgchart-parser-ml-bund-dev```
```json
{
    "action": "analyze-orgchart",
    "parameters": {
        "orgchart_id": "T3JnQ2hhcnROb2RlOjQ=",
        "page": 0
    }
}
```


### Cache all section images related to one orgchart
**Topic:** ```orgchart-image-generator-ml-bund-dev```
```json
{
    "action": "cache-all-orgchart-images",
    "parameters": {
        "orgchart_id": "T3JnQ2hhcnROb2RlOjQ=",
        "page": 0
    }
}
```


## Service Configuration
This service is partly configured via [terraform](https://github.com/bundesAPI/terraform/blob/main/orgchart_ml.tf). The deployment pipeline (via serverless.yaml) needs the following environment variables in its build context:

| Variable                         | Value                                                                                                                |
|----------------------------------|----------------------------------------------------------------------------------------------------------------------|
| CACHE_BUCKET                     | Bucket ARN for image caching bucket                                                                                  |
| ORGCHART_IMAGE_CACHING_SNS_TOPIC | SNS Topic ARN for image caching jobs                                                                                 |
| ORGCHART_PARSER_SNS_TOPIC        | SNS Topic ARN for orgchart analyzer jobs                                                                             |
| SENTRY_DSN                       | sentry monitoring dsn…                                                                                               |
| SENTRY_PROJECT                   | sentry project name (orgchart-ml)                                                                                    |
| SERVICE_DOMAIN                   | backend service domain                                                                                               |
| CLIENT_ID                        | to authenticate as a service via oauth2 client credentials                                                           |
| CLIENT_SECRET                    | to authenticate as a service via oauth2 client credentials                                                           |
| LAMBDA_EXECUTION_ROLE_ARN        | the iam rule that executes the lambda. Needs access to lambda, the buckets, the queues and cloudwatch                |
| DOMAIN                           | the domain this service is running under. Needs to be configured for gateway and already an tls certificate assigned |
