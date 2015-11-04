#! /usr/bin/env python
##########################################################################
# NSAP - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import sys

# Package import
from .trackio import savetxt
from .trackio import loadtxt
from .utils import Tractogram
from .bounded_thinplate_weave import build_bounded_thinplate_module


# At the bottom of the file in the module's 'main' program, an attempt to
# import bounded_thin_plate_ext without building it is made. If this fails (the
# module doesn't exist in the PYTHONPATH), the module is built by calling
# build_bounded_thin_plate_ext(). This approach only takes the time-consuming
# (a few seconds for this example) process of building the module if it
# hasn't been built before.
try:
    import bounded_thinplate
except ImportError:
    build_bounded_thinplate_module()
    import bounded_thinplate


# Add weave functions to module
module_name = __name__ + "." + "bounded_thinplate"
sys.modules[module_name] = bounded_thinplate

