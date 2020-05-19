#!/usr/bin/env python
#############################################################################
##
# This file is part of Taurus
##
# http://taurus-scada.org
##
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
# Taurus is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# Taurus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
##
# You should have received a copy of the GNU Lesser General Public License
# along with Taurus.  If not, see <http://www.gnu.org/licenses/>.
##
#############################################################################

"""Unit tests for Taurus Forms"""

import unittest
from taurus.qt.qtgui.test import GenericWidgetTestCase
from taurus.qt.qtgui.panel import TaurusForm, TaurusAttrForm, TaurusValue
from taurus.core.util.test.test_plugin import mock_entry_point


class TaurusFormTest(GenericWidgetTestCase, unittest.TestCase):
    """
    Generic tests for TaurusForm widget.

    .. seealso: :class:`taurus.qt.qtgui.test.base.GenericWidgetTestCase`
    """
    _klass = TaurusForm
    modelnames = [['sys/tg_test/1'],
                  ['sys/tg_test/1/wave'],
                  [],
                  '',
                  ['eval:1'],
                  None,
                  ['sys/tg_test/1/%s' % a for a in (
                   'short_scalar', 'double_array',
                   'uchar_image_ro', 'string_spectrum',
                   'no_value', 'throw_exception')],
                  [''],
                  'sys/tg_test/1,eval:1',
                  'sys/tg_test/1/short_image eval:rand(16)',
                  [None]
                  ]


class TaurusAttrFormTest(GenericWidgetTestCase, unittest.TestCase):
    """
    Generic tests for TaurusAttrForm widget.

    .. seealso: :class:`taurus.qt.qtgui.test.base.GenericWidgetTestCase`
    """
    _klass = TaurusAttrForm
    modelnames = ['sys/tg_test/1', None]


class _DummyTV(TaurusValue):
    pass


def _DummyItemFactory(m):
    """
    A dummy item factory that returns _DummyTV instance for one specific
    attribute: "eval://localhost/@dummy/'test_itemfactory'"
    """
    if m.fullname == "eval://localhost/@dummy/'test_itemfactory'":
        return _DummyTV()


def test_form_itemFactory():
    """Checks that the TaurusForm itemFactory API works"""
    lines = ["test_Form_ItemFactory={}:_DummyItemFactory".format(__name__)]
    group = "taurus.qt.taurusform.item_factories"
    mock_entry_point(lines, group=group)

    from taurus.qt.qtgui.application import TaurusApplication
    app = TaurusApplication.instance()
    if app is None:
        _ = TaurusApplication([], cmd_line_parser=None)

    w = TaurusForm()
    w.setModel(
        [
            "eval://localhost/@dummy/'test_itemfactory'",
            "eval://localhost/@dummy/'test_itemfactory2'",
        ]
    )
    # The first item should get a customized _DummyTV widget
    assert type(w[0]) is _DummyTV
    # The second item shoud get the default form widget
    assert type(w[1]) is w._defaultFormWidget


def test_form_itemFactory_selection():
    """Checks that the TaurusForm itemFactory selection API works"""
    lines = ["test_Form_ItemFactorySel={}:_DummyItemFactory".format(__name__)]
    group = "taurus.qt.taurusform.item_factories"
    mapping = mock_entry_point(lines, group=group)
    ep1 = mapping[group]["test_Form_ItemFactorySel"]

    from taurus.qt.qtgui.application import TaurusApplication
    app = TaurusApplication.instance()
    if app is None:
        _ = TaurusApplication([], cmd_line_parser=None)

    w = TaurusForm()

    # the test_Form_ItemFactory should be in the default factories
    default_factories = w.getItemFactories()
    assert ep1 in default_factories

    # no factories should be excluded by default
    inc, exc = w.getItemFactories(return_disabled=True)
    assert exc == []

    # Check that we can deselect all factories
    no_factories = w.setItemFactories(include=[])
    assert no_factories == []

    # Check that we can exclude everything except test_Form_ItemFactory
    select1 = w.setItemFactories(
        exclude=[r"(?!.*test_Form_ItemFactorySel).*"]
    )
    assert select1 == [ep1]

    # Check that we can include only test_Form_ItemFactory
    select2 = w.setItemFactories(include=["test_Form_ItemFactorySel"])
    assert select2 == [ep1]

    # Check that the selected test_Form_ItemFactory is an entry point
    from pkg_resources import EntryPoint
    assert type(select2[0]) == EntryPoint

    # Check that the selected entry point loads _DummyItemFactory
    assert select2[0].load() is _DummyItemFactory

    # Check that we can include a factory instance
    select3 = w.setItemFactories(include=[_DummyItemFactory])

    # Check that the selected test_Form_ItemFactory is an entry point-alike
    from taurus.core.util.plugin import EntryPointAlike
    assert type(select3[0]) == EntryPointAlike

    # Check that the selected entry point loads _DummyItemFactory
    assert select3[0].load() is _DummyItemFactory

    # Check that the selected entry point has the given name
    assert select3[0].name == repr(_DummyItemFactory)


