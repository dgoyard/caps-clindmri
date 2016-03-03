##########################################################################
# NSAp - Copyright (C) CEA, 2015 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html for details.
##########################################################################

"""
Package to wrap the Connectomist software and simplify scripting calls.

Each tractography step (i.e. one Connectomist tab) can be run through the use
of a dedicated function of the package.

All the tractography steps can be done at once using the
complete_tractography() function.
"""

from clindmri.extensions.connectomist.manufacturers import MANUFACTURERS
from clindmri.extensions.connectomist.exceptions import (
    ConnectomistError, ConnectomistBadManufacturerNameError,
    ConnectomistMissingParametersError, ConnectomistBadFileError)
