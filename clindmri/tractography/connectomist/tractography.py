##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html for details.
##########################################################################

# System import
import os

# Clindmri import
from clindmri.extensions.connectomist.exceptions import (
    ConnectomistBadFileError, ConnectomistError)
from clindmri.extensions.connectomist import ConnectomistWrapper


bundle_map = {
    "aimsbundlemap": 0,
    "bundlemap": 1,
    "vtkbundlemap": 2,
    "trkbundlemap": 3
}

track_map = {
    "streamline_deterministic": 0,
    "streamline_regularize_deterministic": 1,
    "streamline_probabilistic": 2,
}


def tractography(
        outdir,
        subjectid,
        maskdir,
        model,
        modeldir,
        registrationdir,
        tracking_type="streamline_regularize_deterministic",
        bundlemap="vtkbundlemap",
        min_fiber_length=5.,
        max_fiber_length=300.,
        aperture_angle=30.,
        forward_step=0.2,
        voxel_sampler_point_count=1,
        gibbs_temperature=1.,
        storing_increment=10,
        output_orientation_count=500,
        nb_tries=10,
        path_connectomist=(
            "/i2bm/local/Ubuntu-14.04-x86_64/ptk/bin/connectomist")):
    """ Tractography algorithm.

    Parameters
    ----------
    outdir: str
        path to Connectomist output work directory.
    subjectid: str
        the subject code in study.
    model: str
        the name of the model to be estimated: 'dot', 'sd', 'sdt', 'aqbi',
        'sa-qbi', 'dti'.
    modeldir str
        the path to the Connectomist model directory.
    registrationdir str
        the path to the Connectomist registration directory.
    tracking_type: str (optional, default
            'streamline_regularize_deterministic')
        the tractography algorithm: 'streamline_regularize_deterministic',
        'streamline_deterministic' or 'streamline_probabilistic'
    bundlemap: str (optional, default 'vtkbundlemap')
        the bundle format.
    min_fiber_length: float (optional, default 5)
        the length threshold in mm from which fiber are considered.
    max_fiber_length: float (optional, default 300)
        the length threshold in mm under which fiber are considered.
    aperture_angle: float (optional, default 30)
        the search angle in degrees: for the probabilistic tractography,
        the default connectomist value is 90 degs.
    forward_step: float (optional, default 0.2)
        the propagation step in mm.
    voxel_sampler_point_count: int (optional, default 1)
        the number of seeds per voxel
    gibbs_temperature: float (optional, default 1)
        the temperature if the Gibb's sampler: only for the probabilistic
        tractography.
    storing_increment: int (optional, default 10)
        undersample the fiber with the specified rate.
    output_orientation_count: int (optional, default 500)
        the number of the point in the sphere, default is equivalent to a
        2 degs resolution.
    nb_tries: int (optional, default 10)
        nb of times to try an algorithm if it fails.
        It often crashes when running in parallel. The reason
        why it crashes is unknown.
    path_connectomist: str (optional)
        path to the Connectomist executable.

    Returns
    -------
    outdir: str
        path to Connectomist's output directory.
    """
    # Check input parameters
    if bundlemap not in bundle_map:
        raise ConnectomistError(
            "'{0}' is not a valid bundle format.".format(bundlemap))
    if tracking_type not in track_map:
        raise ConnectomistError(
            "'{0}' is not a valid track algo.".format(tracking_type))

    # Get previous steps files and check existance
    maskfile = os.path.join(maskdir, "tractography_mask.ima")
    odfsitefile = os.path.join(
        modeldir, "{0}_odf_site_map.sitemap".format(model))
    odftexturefile = os.path.join(
        modeldir, "{0}_odf_texture_map.texturemap".format(model))
    odfrgbfile = os.path.join(modeldir, "aqbi_rgb.ima")
    t1file = os.path.join(registrationdir, "t1.ima")
    dwtot1file = os.path.join(registrationdir, "talairach_to_t1.trm")
    masktodwfile = os.path.join(registrationdir, "t1_to_talairach.trm")
    for fpath in (maskfile, odfsitefile, odftexturefile, odfrgbfile, t1file,
                  dwtot1file, masktodwfile):
        if not os.path.isfile(fpath):
            raise ConnectomistBadFileError(fpath)

    # Dict with all parameters for connectomist
    algorithm = "DWI-Tractography"
    parameters_dict = {
        '_subjectName': subjectid,
        'bundleMapFormat': bundle_map[bundlemap],
        'fileNameMask': maskfile,
        'fileNameOdfSiteMap': odfsitefile,
        'fileNameOdfTextureMap': odftexturefile,
        'fileNameRgb': odfrgbfile,
        'fileNameT1': t1file,
        'fileNameTransformationDwToT1': dwtot1file,
        'fileNameTransformationMaskToDw': masktodwfile,
        'outputOrientationCount': output_orientation_count,
        'outputWorkDirectory': outdir,
        'stepCount': 1,
        'trackingType': track_map[tracking_type]}
    parameters_dict.update({
        'deterministicApertureAngle': aperture_angle,
        'deterministicForwardStep': forward_step,
        'deterministicMaximumFiberLength': max_fiber_length,
        'deterministicMinimumFiberLength': min_fiber_length,
        'deterministicStoringIncrement': storing_increment,
        'deterministicVoxelSamplerPointCount': voxel_sampler_point_count})
    parameters_dict.update({
        'probabilisticApertureAngle': aperture_angle,
        'probabilisticForwardStep': forward_step,
        'probabilisticGibbsTemperature': gibbs_temperature,
        'probabilisticMaximumFiberLength': max_fiber_length,
        'probabilisticMinimumFiberLength': min_fiber_length,
        'probabilisticStoringIncrement': storing_increment,
        'probabilisticVoxelSamplerPointCount': voxel_sampler_point_count})
    parameters_dict.update({
        'regularizedDeterministicApertureAngle': aperture_angle,
        'regularizedDeterministicForwardStep': forward_step,
        'regularizedDeterministicLowerGFABoundary': -1.,
        'regularizedDeterministicMaximumFiberLength': max_fiber_length,
        'regularizedDeterministicMinimumFiberLength': min_fiber_length,
        'regularizedDeterministicStoringIncrement': storing_increment,
        'regularizedDeterministicUpperGFABoundary': -1.,
        'regularizedDeterministicVoxelSamplerPointCount': (
            voxel_sampler_point_count)})

    # Call with Connectomist
    connprocess = ConnectomistWrapper(path_connectomist)
    parameter_file = ConnectomistWrapper.create_parameter_file(
        algorithm, parameters_dict, outdir)
    connprocess(algorithm, parameter_file, outdir, nb_tries=nb_tries)

    return outdir
