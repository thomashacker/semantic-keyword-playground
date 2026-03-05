from pydantic import BaseModel
from typing import List, Optional


class DatasetInfo(BaseModel):
    name: str
    description: str
    record_count: int
    fields: List[str]
    seeded: bool = False


class SeedRequest(BaseModel):
    force: bool = False


class SeedResponse(BaseModel):
    dataset: str
    records_loaded: int
    message: str
