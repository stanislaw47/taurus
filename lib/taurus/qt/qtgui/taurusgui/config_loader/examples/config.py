

from taurus.qt.qtgui.taurusgui.utils import PanelDescription, ExternalApp, ToolBarDescription, AppletDescription

GUI_NAME = 'EXAMPLE 01'
ORGANIZATION = 'Taurus'

MANUAL_URI = 'http://www.taurus-scada.org'

SYNOPTIC = ['images/example01.jdw', 'images/syn2.jdw']


INSTRUMENTS_FROM_POOL = False


nxbrowser = PanelDescription(
    'NeXus Browser',
    classname='taurus.qt.qtgui.extra_nexus.TaurusNeXusBrowser'
)

i0 = PanelDescription(
    'BigInstrument',
    classname='taurus.qt.qtgui.panel.TaurusAttrForm',
    model='sys/tg_test/1'
)

i1 = PanelDescription(
    'instrument1',
    classname='taurus.qt.qtgui.panel.TaurusForm',
    model=['sys/tg_test/1/double_scalar',
           'sys/tg_test/1/short_scalar_ro',
           'sys/tg_test/1/float_spectrum_ro',
           'sys/tg_test/1/double_spectrum']
)

i2 = PanelDescription(
    'instrument2',
    classname='taurus.qt.qtgui.panel.TaurusForm',
    model=['sys/tg_test/1/wave',
           'sys/tg_test/1/boolean_scalar']
)

trend = PanelDescription(
    'Trend',
    classname='taurus.qt.qtgui.plot.TaurusTrend',
    model=['sys/tg_test/1/double_scalar']
)

connectionDemo = PanelDescription(
    'Selected Instrument',
    classname='taurus.external.qt.Qt.QLineEdit',  # A pure Qt widget!
    sharedDataRead={'SelectedInstrument': 'setText'},
    sharedDataWrite={'SelectedInstrument': 'textEdited'}
)

dummytoolbar = ToolBarDescription(
    'Empty Toolbar',
    classname='taurus.external.qt.Qt.QToolBar'
)

xterm = ExternalApp(
    cmdargs=['xterm', 'spock'], text="Spock", icon='utilities-terminal')
hdfview = ExternalApp(["hdfview"])
pymca = ExternalApp(['pymca'])

EXTRA_CATALOG_WIDGETS = [
    ('taurus.external.qt.Qt.QLineEdit', 'logos:taurus.png'),  # a resource
    ('taurus.external.qt.Qt.QSpinBox', 'images/syn2.jpg'),  # relative
    # ('taurus.external.Qt.QTextEdit','/tmp/foo.png'),  # absolute
    ('taurus.external.qt.Qt.QLabel', None)]                # none
