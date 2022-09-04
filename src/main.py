import argparse
from tft.config import Config, read_config
import coloredlogs
from logging import info
from tft.api import Scraper

coloredlogs.install(level='DEBUG')

config: Config

def scrape(args, config: Config):
    scraper = Scraper(token=config.riot.token, region=config.scrape.region, cache_dir=config.scrape.cache_dir, sleep=config.scrape.sleep,)
    for league in config.scrape.leagues:
        scraper.scrape_league(league)
    info('scrape')

parser = argparse.ArgumentParser(description='TFT')

parser.add_argument('--config',
                    help='Config file path',
                    nargs='?',
                    default='config.yaml')

subparsers = parser.add_subparsers(help='sub-command help')

p_scrape = subparsers.add_parser('scrape', help='Run scrape')
p_scrape.set_defaults(func=scrape)

args = parser.parse_args()
info(args)
config = read_config(args.config)
info(config)

args.func(args, config)
