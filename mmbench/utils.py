# -*- coding: utf-8 -*-
##########################################################################
# NSAp - Copyright (C) CEA, 2023
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Define utility functions.
"""

# Imports
import types


def listify(data):
    """ Listify input data.
    """
    if isinstance(data, types.GeneratorType):
        return list(data)
    return [data]
