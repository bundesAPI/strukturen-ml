from typing import Union, List, Optional

from pydantic import BaseModel


class OrgchartItem(BaseModel):
    text: str
    position: List[Union[int, float]]
    colors: List[List[int]]
    id: str


class OrgchartSourceItem(BaseModel):
    source: OrgchartItem


class OrgchartParserResult(BaseModel):
    status: str
    items: List[OrgchartSourceItem] = None
    page: int
    method: str


class NamedEntity(BaseModel):
    start: int
    end: int
    label: str


class Person(BaseModel):
    name: Optional[str]
    position: Optional[str]


class Organisation(BaseModel):
    # camel case because frontend :-/
    name: Optional[str]
    shortName: Optional[str]
    dialCodes: Optional[List[str]] = []
    people: Optional[List[Person]] = []


class OrgchartEntryParserResult(BaseModel):
    text: str
    ents: List[NamedEntity]
    parsed: Optional[List[Organisation]]
