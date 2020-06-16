import sys

from . import getLoader


def print_component(p):
    print("\n\tName: " + p.name)
    print("\tClass name: " + p.classname)
    print("\tModule name: " + p.modulename)
    print("\tWidget name: " + str(p.widgetname))
    print("\tFloating: " + str(p.floating))
    print("\tShared data write: " + str(p.sharedDataWrite))
    print("\tShared data read: " + str(p.sharedDataRead))
    print("\tModel: " + str(p.model))


def print_panel(p):
    print_component(p)
    print("\tInstrument key: " + str(p.instrumentkey))
    print("\tIcon: " + str(p.icon))
    print("\tModel in config: " + str(p.model_in_config))
    print("\tModifiable by user: " + str(p.modifiable_by_user))
    print("\tWidget formatter: " + str(p.widget_formatter))
    print("\tWidget properties: " + str(p.widget_properties))


def main(conf):
    l = getLoader(conf)
    l.load()
    print("GUI_NAME: " + str(l.app_name))
    print("ORGANIZATION: " + str(l.org_name))
    print("CUSTOM_LOGO: " + str(l.custom_logo))
    print("ORGANIZATION_LOGO: " + str(l.org_logo))
    print("SINGLE_INSTANCE: " + str(l.single_instance))
    print("MANUAL_URI: " + str(l.manual_uri))
    print("INIFILE: " + str(l.ini_file))
    print("EXTRA_CATALOG_WIDGETS")
    for w, i in l.extra_catalog_widgets:
        print("\tWidget: " + str(w) + ", icon: " + str(i))
    print("SYNOPTIC: " + str(l.synoptics))
    print("CONSOLE: " + str(l.console))
    print("PanelDescriptions: ")
    for p in l.panels:
        print_panel(p)
    print("ToolBarDescriptions: ")
    for p in l.toolbars:
        print_component(p)
    print("AppletDescriptions: ")
    for p in l.applets:
        print_component(p)
    print("ExternalApp: ")
    for p in l.external_apps:
        print("\t" + str(p))


main(sys.argv[1])
