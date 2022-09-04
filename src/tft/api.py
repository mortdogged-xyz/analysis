from dataclasses import dataclass
from logging import info
from pydantic import BaseModel
import requests
import json
import time
import hashlib
import os
import glob
import pandas as pd

class Region(BaseModel):
    region: str
    gateway: str


__REGIONS__ = {
    "NA": Region(region="na1", gateway="americas"),
    "CN": Region(region="cn1", gateway="asia"),
}

@dataclass
class Scraper:
    token: str
    cache_dir: str
    region: str = "NA"
    sleep: int = 1


    def region_cfg(self) -> Region:
        return __REGIONS__[self.region]

    def __get__(self, routing: str, path: str, cache_key: str = "get"):
        url = f"https://{routing}.api.riotgames.com/{path}"
        hash = hashlib.md5(url.encode("utf-8")).hexdigest()
        fname = f"{cache_key}-{hash}.json"
        fpath = f"{self.cache_dir}/{fname}"
        if os.path.exists(fpath):
            with open(fpath, 'r') as f:
                info(f"Reading {fpath}")
                data = json.loads(f.read())
                return data

        headers = {"X-Riot-Token": self.token}
        resp = requests.get(url, headers=headers)
        data = resp.json()

        with open(fpath, 'w') as f:
            info(f"Writing {fpath}")
            json.dump(data, f)

        time.sleep(self.sleep)
        return data

    def get_league(self, league: str):
        return self.__get__(self.region_cfg().region, f"tft/league/v1/{league}")

    def get_summoner(self, id: str):
        return self.__get__(self.region_cfg().region, f"tft/summoner/v1/summoners/{id}", cache_key="summoner",)

    def get_matches_for(self, puuid: str):
        return self.__get__(self.region_cfg().gateway, f"tft/match/v1/matches/by-puuid/{puuid}/ids", cache_key="summoner",)

    def get_match(self, id: str):
        return self.__get__(self.region_cfg().gateway, f"tft/match/v1/matches/{id}", cache_key="match",)

    def scrape_league(self, league: str):
        league_data = self.get_league(league)
        summoners = list(map(lambda d: d["summonerId"], league_data["entries"]))
        info(len(summoners))
        all_matches = []
        for summoner in summoners:
            summoner_data = self.get_summoner(summoner)
            matches_ids = self.get_matches_for(summoner_data["puuid"])
            all_matches.extend(matches_ids)

        info(f"Scraping {len(all_matches)} matches")
        for match_id in all_matches:
            self.get_match(match_id)

@dataclass
class DataImporter:
    cache_dir: str
    data_dir: str

    def import_all(self):
        files = glob.glob(f"{self.cache_dir}/match-*.json")
        info(files)

        for file in files:
            with open(file, 'r') as f:
                df = pd.read_json(f)
                info(df.head())
            return
