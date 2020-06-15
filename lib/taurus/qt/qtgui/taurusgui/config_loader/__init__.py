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
###########################################################################

"""
This module provides factory 'getLoader' for proper ConfigLoader object
detected from 'confname' string. Each config loader has to implement interface
defined by AbstractConfigLoader class in
taurus.qt.qtgui.taurusgui.config_loader.abstract
"""

import os

import pkg_resources


__all__ = ["getLoader"]


def getLoader(confname):
    """
    Discover proper config loader based on passed string.
    It can be either path to file or directory or Python
    abolute path to module with configuration.

    :param confname: name of configuration
    :return: A AbstractConfigLoader subclass object
    """

    if os.path.exists(confname):
        if os.path.isfile(confname):  # happy path, we got file

            # get file extension without dot
            ext = os.path.splitext(confname)[-1][1:]

            klass = _get_plugin_from_entrypoint(ext, "taurus.gui.loader")
            if klass is None:
                raise NotImplementedError(
                    "Not supported config file format: '%s'" % ext
                )
            else:
                return klass(confname)

        elif os.path.isdir(confname):
            # if it's directory, assume it's importable Python package
            from .pyconf import PyConfigLoader

            return PyConfigLoader(confname)
        else:
            raise ValueError("Not file or directory: '%s'" % confname)
    else:
        # not path, assume it's importable Python package path
        from .pyconf import PyConfigLoader

        return PyConfigLoader(confname)


def _get_plugin_from_entrypoint(name, entry_point):
    """
    Load value of entry point as plugin.
    Exceptions are not caught on purpose - propagate them up the stack.

    :param name: name of plugin
    :param entry_point: dotted name of entry-point loading space
    :return: entry point value if found, None otherwise
    """

    for ep in pkg_resources.iter_entry_points(entry_point):
        if ep.name == name:
            ep_value = ep.load()
            return ep_value
    return None
