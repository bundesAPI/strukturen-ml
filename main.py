import json
import os
import uuid
from io import BytesIO
from typing import Optional, List, Union

import requests
from fastapi import FastAPI, HTTPException, Query
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse, Response
import logging

from cache import S3Cache
from models import OrgchartParserResult, OrgchartItem, OrgchartEntryParserResult
from orgchart import OrgchartParser, deduplicate_entries
from orgchart_entry import OrgChartEntryParser
from queries import ORG_CHART_QUERY, UPDATE_ORG_CHART
from sns import generate_image_sns
from utils import get_client
from fastapi_utils.timing import add_timing_middleware, record_timing

AWS_LAMBDA_FUNCTION_NAME = os.getenv("AWS_LAMBDA_FUNCTION_NAME", None)
AWS_REGION = os.getenv("AWS_REGION", None)
AWS_VERSION = os.getenv("AWS_LAMBDA_FUNCTION_VERSION", None)
CACHE_BUCKET = os.getenv("CACHE_BUCKET", None)

if CACHE_BUCKET:
    CACHE = S3Cache(CACHE_BUCKET)
else:
    CACHE = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Strukturen-ML",
    description="Orgchart PDF Document Analysis",
    version=f"{AWS_REGION}:{AWS_LAMBDA_FUNCTION_NAME}:{AWS_VERSION}",
    contact={
        "name": "bund.dev on Github",
        "url": "https://github.com/bundesAPI/strukturen-ml",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_timing_middleware(app, record=logger.info, prefix="app", exclude="untimed")


# TODO remove local dev credentials
CLIENT_ID = os.getenv("CLIENT_ID", "oql40oIDbnsAdxH7btZVLRPagZbFPBp5itukk1NB")
CLIENT_SECRET = os.getenv(
    "CLIENT_SECRET",
    "VIZRSVjeBHSaOES3CJZ8eNsf0i6PPPGHGisuvlApZ3sL4Ef9DU2OLf4uATkwhrXzlLwd75IFYay7CxHYb56ZbllwmVG9083yilIB9Vn62AN9drAPLLWERVLc2O9OV1q4",
)
DOMAIN = os.getenv("SERVICE_DOMAIN", "http://127.0.0.1:8000")
MEDIA_DOMAIN = os.getenv("MEDIA_DOMAIN", None)
ORGCHART_IMAGE_CACHING_SNS_TOPIC = os.getenv("ORGCHART_IMAGE_CACHING_SNS_TOPIC", None)


ORG_CHART_ENTRY_PARSER = OrgChartEntryParser()


@app.get("/analyze-orgchart-entry/", response_model=OrgchartEntryParserResult)
def analyze_orgchart_item(text: str):
    nlp, result = ORG_CHART_ENTRY_PARSER.parse(text)
    result["parsed"] = ORG_CHART_ENTRY_PARSER.parse_to_entities(nlp)
    return result


@app.get("/orgchart-image/", response_class=Response(media_type="image/png"))
def get_orgchart_image(
    orgchart_id: str,
    page: Optional[int],
    position: Optional[List[Union[float, int]]] = Query([]),
):
    """
    render an orgchart pdf as an image
    :param orgchart_id: the id of the orgchart in the backend
    :param page: the page the orgchart is on (default 0) TODO: auto-detection
    :param position: optional section of the orgchart that should be rendered
    :return: the rendered image
    """
    client = get_client(DOMAIN, CLIENT_ID, CLIENT_SECRET)
    chart = client.execute(ORG_CHART_QUERY, variable_values={"id": orgchart_id})
    logger.info("Fetched Orgchart")

    if not chart["orgChart"]:
        raise HTTPException(status_code=404, detail="OrgChart not found")

    # check if item is in cache and return if exsist
    cache_key = (
        orgchart_id + "-" + str(page) + "-" + "-".join([str(p) for p in position])
    )
    if CACHE:
        item = CACHE.get_item(cache_key)
        if item:
            return StreamingResponse(item, media_type="image/png")

    # fetch orgchart as pdf
    if MEDIA_DOMAIN:
        url = f'{MEDIA_DOMAIN}{chart["orgChart"]["document"]}'
    else:
        url = chart["orgChart"]["document"]
    blob = requests.get(url, stream=True)
    parser = OrgchartParser(BytesIO(blob.content), page=page)
    file_obj = BytesIO()

    # parse orgchart
    if len(position) == 4:
        logger.info("Export Image")
        parser.get_image(position).save(file_obj, format="PNG")
    else:
        logger.info("Export Image")
        parser.page.to_image(resolution=144).save(file_obj, format="PNG")
    file_obj.seek(0)
    if CACHE:
        CACHE.set_item(cache_key, file_obj)
        file_obj.seek(0)
    return StreamingResponse(file_obj, media_type="image/png")


@app.get("/cache-preview-images/")
def cache_all_orgchart_images(orgchart_id: str, page: Optional[int] = 0):
    """
    cache all orgchart preview images related to one orgchart
    """
    client = get_client(DOMAIN, CLIENT_ID, CLIENT_SECRET)
    chart = client.execute(ORG_CHART_QUERY, variable_values={"id": orgchart_id})

    if not chart["orgChart"]:
        raise HTTPException(status_code=404, detail="OrgChart not found")
    print(chart)
    orgchart_source = json.loads(chart["orgChart"]["rawSource"])
    logger.info("Fetched Orgchart")

    # fetch orgchart as pdf
    if MEDIA_DOMAIN:
        url = f'{MEDIA_DOMAIN}{chart["orgChart"]["document"]}'
    else:
        url = chart["orgChart"]["document"]
    blob = requests.get(url, stream=True)
    parser = OrgchartParser(BytesIO(blob.content), page=page)
    img = parser.page.to_image(resolution=144)

    for item in orgchart_source["items"]:
        position = item["position"]
        cache_key = (
            orgchart_id + "-" + str(page) + "-" + "-".join([str(p) for p in position])
        )
        imgb = BytesIO()
        croped = img.original.crop(position)
        croped.save(imgb, format="PNG", quality=90)
        imgb.seek(0)
        if CACHE:
            CACHE.set_item(cache_key, imgb)
    return {}


@app.get("/analyze-orgchart/", response_model=OrgchartParserResult)
def analyze_orgchart(orgchart_id: str, page: Optional[int]):
    """
    analyze an orgchart pdf file with multiple strategies (finding elements by pdf parsing and opencv). If an element has not been parsed yet it will be stored.
    :param orgchart_id: id of the orgchart
    :param page: page number that should be analyzed
    :return: the analyzed orgchart as json
    """
    client = get_client(DOMAIN, CLIENT_ID, CLIENT_SECRET)
    chart = client.execute(ORG_CHART_QUERY, variable_values={"id": orgchart_id})
    if not chart["orgChart"]:
        raise HTTPException(status_code=404, detail="OrgChart not found")
    if MEDIA_DOMAIN:
        url = f'{MEDIA_DOMAIN}{chart["orgChart"]["document"]}'
    else:
        url = chart["orgChart"]["document"]

    blob = requests.get(url, stream=True)
    parser = OrgchartParser(BytesIO(blob.content), page=page)

    pdf_analysis = deduplicate_entries(parser.analyze_pdf())
    opencv_analysis = deduplicate_entries(parser.analyze_opencv())
    if len(opencv_analysis) > len(pdf_analysis):
        method = "opencv"
        analyzed_items = parser.analyze_primary_colours(opencv_analysis)
    else:
        method = "pdf"
        analyzed_items = parser.analyze_primary_colours(pdf_analysis)

    items = []
    for itm in analyzed_items:
        items.append(
            OrgchartItem(
                position=itm["position"],
                colors=itm["colors"],
                text=itm["text"],
                id=str(uuid.uuid4()),
            )
        )

    result = OrgchartParserResult(status="ok", items=items, page=page, method=method)

    # if the element is not yet marked as imported
    if chart["orgChart"]["status"] == "NEW":
        client.execute(
            UPDATE_ORG_CHART,
            variable_values={
                "orgChartId": orgchart_id,
                "status": "PARSED",
                "rawSource": result.json(),
            },
        )
    return result
