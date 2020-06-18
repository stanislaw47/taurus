import sys
from pprint import pprint

from .util import getLoaders


def main(conf):
    cfg = {}
    loaders = getLoaders(conf)
    for loader in loaders:
        cfg.update(loader.load())
    cfg["PanelDescriptions"] = [p.to_dict() for p in cfg.get("PanelDescriptions", [])]
    cfg["ToolbarDescriptions"] = [p.to_dict() for p in cfg.get("ToolbarDescriptions", [])]
    cfg["AppletDescriptions"] = [p.to_dict() for p in cfg.get("AppletDescriptions", [])]
    cfg["ExternalApps"] = [p.to_dict() for p in cfg.get("ExternalApps", [])]
    pprint(cfg)


main(sys.argv[1])
