import sys
from pprint import pprint

from .util import getLoaders


def main(conf):
    cfg = {}
    loaders = getLoaders(conf)
    for loader in loaders:
        cfg.update(loader.load())
    pprint(cfg)


main(sys.argv[1])
