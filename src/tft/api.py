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

def select_keys(coll, keys, rename = dict()):
    return dict((rename.get(k, k), v) for k, v in coll.items() if k in keys)

@dataclass
class DataImporter:
    cache_dir: str
    data_dir: str

    def import_all(self):
        files = glob.glob(f"{self.cache_dir}/match-*.json")
        info(len(files))
        all_data = []
        m_data = []
        p_data = []
        a_data = []
        t_data = []
        u_data = []
        i_data = []

        for file in files:
            with open(file, 'r') as f:
                m = json.loads(f.read())
                all_data.append(m)

        for m in all_data:
            match = {
                'match_id': m['metadata']['match_id'],
                'match_length': m['info']['game_length'],
            }
            m_data.append(match)

            for p in m['info']['participants']:
                participant = select_keys(p, [
                    'puuid'
                ])
                participant_data = select_keys(p, [
                    'placement',
                    'level',
                    'total_damage_to_players',
                    'last_round',
                ])
                p_data.append(participant_data | participant | match)

                for a in p['augments']:
                    a_data.append({'augment': a} | participant | match)

                for t in p['traits']:
                    trait = select_keys(t, [
                        'name',
                        'num_units',
                        'style',
                        'tier_current',
                        'tier_total',
                    ], {
                        'name': 'trait'
                    })
                    t_data.append(trait | participant | match)

                for u in p['units']:
                    unit = select_keys(u, [
                        'character_id',
                    ])
                    unit_data = select_keys(u, [
                        'name',
                        'rarity',
                        'tier',
                    ], {
                        'name': 'character_name'
                    })
                    u_data.append(unit | unit_data | participant | match)

                    for i in u['itemNames']:
                        i_data.append({'item': i} | unit | participant | match)

        matches_df = pd.DataFrame(m_data)
        participants_df = pd.DataFrame(p_data)
        aug_df = pd.DataFrame(a_data)
        trait_df = pd.DataFrame(t_data)
        unit_df = pd.DataFrame(u_data)
        item_df = pd.DataFrame(i_data)

        print(matches_df)
        print(participants_df)
        print(aug_df)
        print(trait_df)
        print(unit_df)
        print(item_df)

        self.to_file(matches_df, "matches")
        self.to_file(participants_df, "participants")
        self.to_file(aug_df, "augments")
        self.to_file(trait_df, "traits")
        self.to_file(unit_df, "units")
        self.to_file(item_df, "items")
    
    def to_file(self, df: pd.DataFrame, fname: str):
        path = f"{self.data_dir}/{fname}.csv"
        info(f"Writing {path}")
        df.to_csv(path, index=False)

