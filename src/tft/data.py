import glob
import json
import pandas as pd
import numpy as np
from logging import info, error
from dataclasses import dataclass
from typing import List, Optional
from tqdm import tqdm


def select_keys(coll, keys, rename=dict()):
    return dict((rename.get(k, k), v) for k, v in coll.items() if k in keys)


@dataclass
class DataExporter:
    cache_dir: str
    data_dir: str

    def export_all(self):
        files = glob.glob(f"{self.cache_dir}/match-*.json")

        all_data = []
        m_data = []
        p_data = []
        a_data = []
        t_data = []
        u_data = []
        i_data = []

        info(f"Exporting {len(files)} match files")
        for fname in tqdm(files):
            with open(fname, 'r') as f:
                m = json.loads(f.read())
                all_data.append((fname, m))

        info(f"Exporting {len(all_data)} match results")
        for (fname ,m) in tqdm(all_data):
            try:
                match = {
                    'match_id': m['metadata']['match_id'],
                    'match_datetime': m['info']['game_datetime'],
                    'match_length': m['info']['game_length'],
                    'tft_set_number': m['info']['tft_set_number'],
                    'tft_set_name': m['info']['tft_set_core_name'],
                }
                m_data.append(match)

                for p in m['info']['participants']:
                    participant = select_keys(p, [
                        'puuid',
                        'placement',
                    ])
                    participant_data = select_keys(p, [
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
                        ], {'name': 'trait'})
                        t_data.append(trait | participant | match)

                    for u in p['units']:
                        unit = select_keys(u, [
                            'character_id',
                        ])
                        unit_data = select_keys(u, [
                            'name',
                            'rarity',
                            'tier',
                        ], {'name': 'character_name'})
                        u_data.append(unit | unit_data | participant | match)

                        for i in u['itemNames']:
                            i_data.append({'item': i} | unit | participant | match)
            except Exception as e:
                error(f"Colud not process {fname}")
                error(e)

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

    def load_all(self, files: List[str] = [], days_cutoff: int = 7, set_name: Optional[str] = None):
        files = files or [
            "participants",
            "augments",
            "traits",
            "units",
            "items",
        ]

        data = {}
        for f in tqdm(files):
            path = f"{self.data_dir}/{f}.csv"
            df = pd.read_csv(path, index_col=['match_id', 'puuid'])

            # parse date time
            df['match_datetime'] = pd.to_datetime(df['match_datetime'], unit='ms', origin='unix')

            # filter matches since n days
            since = np.datetime64('now') - np.timedelta64(days_cutoff, 'D')
            df = df[df['match_datetime'] >= since]

            # filter by set
            if set_name:
                df = df[df['tft_set_name'] == set_name]

            data[f] = df

        dt = Data(**data)
        return dt
