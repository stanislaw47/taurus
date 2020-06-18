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


import pkg_resources

from taurus import warning


__all__ = ["getLoaders"]


def getLoaders(confname):
    """
    Discover proper config loader based on passed string.
    It can be either path to file or directory or Python
    abolute path to module with configuration.

    :param confname: name of configuration
    :return: A AbstractConfigLoader subclass object
    """

    EP_GROUP_LOADERS = "taurus.gui.loaders"

    loaders = []
    for ep in pkg_resources.iter_entry_points(EP_GROUP_LOADERS):
        try:
            loader = ep.load()
            if loader.supports(confname):
                loaders.append(loader(confname))
        except Exception as e:
            warning(
                "Could not load config loader plugin '%s. Reason: '%s",
                ep.name,
                e,
            )
    if not loaders:
        raise NotImplementedError(
            "No supported config loader for '%s'" % confname
        )
    else:
        return loaders
