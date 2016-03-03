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


odf_model_map = {
    "dot": 0,
    "sd": 3,
    "sdt": 4,
    "aqbi": 5,
    "sa-aqbi": 6,
    "dti": 7
}

dti_estimator_map = {
    "linear": 0,
    "positive": 1
}

sd_kernel_map = {
    "symmetric_tensor": 0,
    "normal": 1
}


def dwi_local_modeling(
        outdir,
        registered_dwi_dir,
        subjectid,
        model="aqbi",
        order=4,
        aqbi_laplacebeltrami_sharpefactor=0.0,
        regularization_lccurvefactor=0.006,
        dti_estimator="linear",
        constrained_sd=False,
        sd_kernel_type="symmetric_tensor",
        sd_kernel_lower_fa=0.65,
        sd_kernel_upper_fa=0.85,
        sd_kernel_voxel_count=300,
        nb_tries=10,
        path_connectomist=(
            "/i2bm/local/Ubuntu-14.04-x86_64/ptk/bin/connectomist")):
    """ Diffusion model estimation.

    Parameters
    ----------
    outdir: str
        path to Connectomist output work directory.
    registered_dwi_dir: str
        path to Connectomist registeres DWI directory.
    subjectid: str
        the subject code in study.
    model: str (optional, default 'aqbi')
        the name of the model to be estimated: 'dot', 'sd', 'sdt', 'aqbi',
        'sa-qbi', 'dti'.
    order: int (optional, default 4)
        the order of the desired model which is directly related to the
        nulber of maxima that can be modeled considering the data SNR. For
        'dti' model this parameter has no effect since it is by definition a
        second order model
    aqbi_laplacebeltrami_sharpefactor: float (optional default 0.0)
        for 'aqbi' and 'sa-aqbi' sharpening factor.
    regularization_lccurvefactor: float (optional default 0.006)
        for 'sdt', 'aqbi' and 'sa-aqbi' regularization factor.
    dti_estimator: str (optional default 'linear')
        the secend order tensor fitting method: 'linear' or 'positive'.
        The seconf method generates positive definite tensors.
    constrained_sd: bool (optiona, default False)
        If True us constrained spherical deconvolution.
    sd_kernel_type: str (optional, default 'symmetric_tensor')
        the spherical deconvolution kernel type: 'symmetric_tensor' or
        'normal'.
    sd_kernel_lower_fa: float (optional, default 0.65)
        lower fractional anisotrpy threshold.
    sd_kernel_upper_fa: float (optional, default 0.85)
        upper fractional anisotrpy threshold.
    sd_kernel_voxel_count: int (optional, default 300)
        kernel size in voxels.
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
    # Get Connectomist registration result files and check existance
    dwifile = os.path.join(registered_dwi_dir, "dw_talairach.ima")
    maskfile = os.path.join(registered_dwi_dir, "mask_talairach.ima")
    t1file = os.path.join(registered_dwi_dir, "t1.ima")
    t2file = os.path.join(registered_dwi_dir, "t2_talairach.ima")
    dwtot1file = os.path.join(registered_dwi_dir, "talairach_to_t1.trm")
    for fpath in (dwifile, maskfile, t1file, t2file, dwtot1file):
        if not os.path.isfile(fpath):
            raise ConnectomistBadFileError(fpath)

    # Check input parameters
    if model not in odf_model_map:
        raise ConnectomistError("'{0}' model not supported.".format(model))
    if dti_estimator not in dti_estimator_map:
        raise ConnectomistError("'{0}' dti estimator not supported.".format(
            dti_estimator))
    if not isinstance(constrained_sd, bool):
        raise ConnectomistError("'constrained_sd' is not a boolean.")
    constrained_sd = int(constrained_sd)
    if sd_kernel_type not in sd_kernel_map:
        raise ConnectomistError("'{0}' kernel not supported.".format(
            sd_kernel_type))

    # Dict with all parameters for connectomist
    algorithm = "DWI-Local-Modeling"
    parameters_dict = {
        '_subjectName': subjectid,
        'odfType': odf_model_map[model],
        'viewType': odf_model_map[model],
        'computeOdfVolume': 0,
        'rgbScale': 1.0,
        'outputOrientationCount': 500,
        'outputWorkDirectory': outdir,
        'fileNameDw': dwifile,
        'fileNameMask': maskfile,
        'fileNameT1': t1file,
        'fileNameT2': t2file,
        'fileNameTransformationDwToT1': dwtot1file}
    parameters_dict.update({
        'aqbiLaplaceBeltramiSharpeningFactor': (
            aqbi_laplacebeltrami_sharpefactor),
        'aqbiMaximumSHOrder': order,
        'aqbiRegularizationLcurveFactor': regularization_lccurvefactor})
    parameters_dict.update({
        'dotEffectiveDiffusionTime': 25.0,
        'dotMaximumSHOrder': order,
        'dotOdfComputation': 2,
        'dotR0': 12.0})
    parameters_dict.update({
        'dsiFilteringDataBeforeFFT': 2,
        'dsiMarginalOdf': 2,
        'dsiMaximumR0': 15.0,
        'dsiMinimumR0': 1.0})
    parameters_dict.update({
        'dtiEstimatorType': dti_estimator_map[dti_estimator]})
    parameters_dict.update({
        'qbiEquatorPointCount': 50,
        'qbiPhiFunctionAngle': 0.0,
        'qbiPhiFunctionMaximumAngle': 0.0,
        'qbiPhiFunctionType': 0})
    parameters_dict.update({
        'saAqbiLaplaceBeltramiSharpeningFactor': (
            aqbi_laplacebeltrami_sharpefactor),
        'saAqbiMaximumSHOrder': order,
        'saAqbiRegularizationLcurveFactor': regularization_lccurvefactor})
    parameters_dict.update({
        'sdFilterCoefficients': (
            '1 1 1 0.5 0.1 0.02 0.002 0.0005 0.0001 0.00010.00001 0.00001 '
            '0.00001 0.00001 0.00001 0.00001 0.00001'),
        'sdKernelLowerFAThreshold': sd_kernel_lower_fa,
        'sdKernelType': sd_kernel_map[sd_kernel_type],
        'sdKernelUpperFAThreshold': sd_kernel_upper_fa,
        'sdKernelVoxelCount': sd_kernel_voxel_count,
        'sdMaximumSHOrder': order,
        'sdUseCSD': constrained_sd})
    parameters_dict.update({
        'sdtKernelLowerFAThreshold': sd_kernel_lower_fa,
        'sdtKernelType': sd_kernel_map[sd_kernel_type],
        'sdtKernelUpperFAThreshold': sd_kernel_upper_fa,
        'sdtKernelVoxelCount': sd_kernel_voxel_count,
        'sdtMaximumSHOrder': order,
        'sdtRegularizationLcurveFactor': regularization_lccurvefactor,
        'sdtUseCSD': constrained_sd})

    # Call with Connectomist
    connprocess = ConnectomistWrapper(path_connectomist)
    parameter_file = ConnectomistWrapper.create_parameter_file(
        algorithm, parameters_dict, outdir)
    connprocess(algorithm, parameter_file, outdir, nb_tries=nb_tries)

    return outdir
