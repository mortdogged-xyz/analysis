import argparse
from tft.config import Config, read_config
import coloredlogs
from logging import info
from tft.api import Scraper, DataExporter

coloredlogs.install(level='DEBUG')

config: Config

def scrape(args, config: Config):
    scraper = Scraper(token=config.riot.token, region=config.scrape.region, cache_dir=config.scrape.cache_dir, sleep=config.scrape.sleep,)
    for league in config.scrape.leagues:
        scraper.scrape_league(league)

def export(args, config: Config):
    exporter = DataExporter(cache_dir=config.scrape.cache_dir, data_dir=config.scrape.data_dir,)
    exporter.import_all()

parser = argparse.ArgumentParser(description='TFT')

parser.add_argument('--config',
                    help='Config file path',
                    nargs='?',
                    default='config.yaml')

subparsers = parser.add_subparsers(help='sub-command help')

p_scrape = subparsers.add_parser('scrape', help='Run scrape')
p_scrape.set_defaults(func=scrape)

p_export = subparsers.add_parser('export', help='Export json to csv')
p_export.set_defaults(func=export)

args = parser.parse_args()
info(args)
config = read_config(args.config)
info(config)

args.func(args, config)
