import glob
import json
import pandas as pd
from logging import info
from dataclasses import dataclass
from typing import List

def select_keys(coll, keys, rename = dict()):
    return dict((rename.get(k, k), v) for k, v in coll.items() if k in keys)

@dataclass
class DataExporter:
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



@dataclass
class Data:
    participants: pd.DataFrame
    augments: pd.DataFrame
    traits: pd.DataFrame
    units: pd.DataFrame
    items: pd.DataFrame

@dataclass
class DataLoader:
    data_dir: str

    def load_all(self, files: List[str] = []):
        files = files or [
            "participants",
            "augments",
            "traits",
            "units",
            "items",
        ]
        data = {}
        for f in files:
            path = f"{self.data_dir}/{f}.csv"
            df = pd.read_csv(path, index_col=['match_id', 'puuid'])
            data[f] = df
        dt = Data(**data)
        print(dt)
