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
**Topic:** ```orgchart-image-generator-ml-bund-dev```
```json
{
    "action": "analyze-orgchart",
    "parameters": {
        "orgchart_id": "T3JnQ2hhcnROb2RlOjQ=",
        "page": 0,
        "position": [78, 590, 131, 645]
    }
}
```