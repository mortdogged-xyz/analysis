import yaml
from pydantic import BaseModel
from typing import List 

class ScrapeConfig(BaseModel):
    region: str
    cache_dir: str
    sleep: int
    leagues: List[str]

class RiotConfig(BaseModel):
    token: str

class Config(BaseModel):
    riot: RiotConfig
    scrape: ScrapeConfig

def read_config(fname) -> Config:
    with open(fname, 'r') as stream:
        return Config(**yaml.safe_load(stream))
