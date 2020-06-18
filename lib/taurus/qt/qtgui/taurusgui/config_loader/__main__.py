import sys
from pprint import pprint

from .util import getLoaders


def main(conf):
    cfg = {}
    loaders = getLoaders(conf)
    for loader in loaders:
        cfg.update(loader.load())
    # pprint(cfg)
    panels = [p.to_dict() for p in cfg.get("PanelDescriptions", [])]
    cfg["PanelDescriptions"] = panels

    toolbars = [p.to_dict() for p in cfg.get("ToolBarDescriptions", [])]
    cfg["ToolBarDescriptions"] = toolbars

    applets = [p.to_dict() for p in cfg.get("AppletDescriptions", [])]
    cfg["AppletDescriptions"] = applets

    ext_app = [p.to_dict() for p in cfg.get("ExternalApps", [])]
    cfg["ExternalApps"] = ext_app

    pprint(cfg)


main(sys.argv[1])
