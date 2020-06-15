import sys

from . import getLoader


l = getLoader(sys.argv[1])
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
    print("\t" + str(p))
print("ToolBarDescriptions: ")
for p in l.toolbars:
    print("\t" + str(p))
print("AppletDescriptions: ")
for p in l.applets:
    print("\t" + str(p))
print("ExternalApp: ")
for p in l.external_apps:
    print("\t" + str(p))
