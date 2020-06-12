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

""""""

import os


__all__ = ["getLoader"]


def getLoader(confname):
    ext = os.path.splitext(confname)[-1]

    if os.path.isdir(confname) or ext == ".py":
        from .pyconf import PyConfigLoader
        return PyConfigLoader(confname)
    elif ext == ".xml":
        from .xmlconf import XmlConfigLoader
        return XmlConfigLoader(confname)
    elif ext == ".json":
        from .jsonconf import JsonConfigLoader
        return JsonConfigLoader(confname)
    else:
        raise NotImplementedError("No config loader implementation for '%s'" % ext)
