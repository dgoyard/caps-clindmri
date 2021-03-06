#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013-2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import print_function
import argparse
import os
import shutil

# Bredala import
try:
    import bredala
    bredala.USE_PROFILER = False
    bredala.register(
        "clindmri.tractography.connectomist.complete_tractography",
        names=["complete_tractography"])
    bredala.register(
        "clindmri.tractography.connectomist.dwi_local_modeling",
        names=["dwi_local_modeling"])
    bredala.register(
        "clindmri.tractography.connectomist.mask",
        names=["tractography_mask"])
    bredala.register(
        "clindmri.tractography.connectomist.tractography",
        names=["tractography"])
except:
    pass

# Clindmri import
from clindmri.tractography.connectomist.complete_tractography import (
    complete_tractography)


# Parameters to keep trace
__hopla__ = ["outdir", "subjectid", "preprocdir", "morphologistdir"]

# Script documentation
doc = """
Connectomist tractography
~~~~~~~~~~~~~~~~~~~~

Function that runs all the Connectomist tractography tabs.

Steps:

1- Create the tractography output directory if not existing.
2- Detect the Connectomist registration folder.
3- Compute the diffusion model.
4- Create the tractography mask.
5- The tractography algorithm.

Command:

python $HOME/git/caps-clindmri/clindmri/scripts/connectomist_tractography.py \
    -v 2 \
    -o /tmp/morphologist/connectomist \
    -g /neurospin/senior/nsap/data/V0/morphologist \
    -s ab130187 \
    -e
"""


def is_file(filearg):
    """ Type for argparse - checks that file exists but does not open.
    """
    if not os.path.isfile(filearg):
        raise argparse.ArgumentError(
            "The file '{0}' does not exist!".format(filearg))
    return filearg


def is_directory(dirarg):
    """ Type for argparse - checks that directory exists.
    """
    if not os.path.isdir(dirarg):
        raise argparse.ArgumentError(
            "The directory '{0}' does not exist!".format(dirarg))
    return dirarg


parser = argparse.ArgumentParser(description=doc)
parser.add_argument(
    "-v", "--verbose", dest="verbose", type=int, choices=[0, 1, 2], default=0,
    help="increase the verbosity level: 0 silent, [1, 2] verbose.")
parser.add_argument(
    "-e", "--erase", dest="erase", action="store_true",
    help="if activated, clean the subject folder.")
parser.add_argument(
    "-o", "--outdir", dest="outdir", required=True, metavar="PATH",
    help="the Connectomist tractography home directory.", type=is_directory)
parser.add_argument(
    "-s", "--subjectid", dest="subjectid", required=True,
    help="the subject identifier.")
parser.add_argument(
    "-p", "--preprocdir", dest="preprocdir", metavar="PATH",
    help="the path to the diffusion preprocessings.", type=is_directory)
parser.add_argument(
    "-g", "--morphologistdir", dest="morphologistdir", required=True,
    metavar="PATH", help="the path to the morphologist processings.",
    type=is_directory)
args = parser.parse_args()


"""
First check if the subject Connectomist directory exists on the file system,
and clean it if requested.
"""
if args.verbose > 0:
    print("[info] Start Connectomist tractography...")
    print("[info] Directory: {0}.".format(args.outdir))
    print("[info] Subject: {0}.".format(args.subjectid))
    print("[info] Preproc: {0}.".format(args.preprocdir))
outdir = args.outdir
subjectid = args.subjectid
subjdir = os.path.join(args.outdir, subjectid, "tractography")
preprocdir = args.preprocdir
morphologistdir = args.morphologistdir
if preprocdir is None:
    preprocdir = os.path.join(args.outdir, subjectid, "preproc")
if not os.path.isdir(subjdir):
    os.makedirs(subjdir)
elif os.path.isdir(subjdir) and args.erase:
    shutil.rmtree(subjdir)
    os.mkdir(subjdir)

"""
Connectomist tractography: all steps
"""
complete_tractography(
        subjdir,
        preprocdir,
        morphologistdir,
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
        add_cerebelum=False,
        add_commissures=True,
        tracking_type="streamline_regularize_deterministic",
        bundlemap="vtkbundlemap",
        min_fiber_length=5.,
        max_fiber_length=300.,
        aperture_angle=30.,
        forward_step=0.2,
        voxel_sampler_point_count=8,
        gibbs_temperature=1.,
        storing_increment=10,
        output_orientation_count=500,
        nb_tries=10,
        path_connectomist=(
            "/i2bm/local/Ubuntu-14.04-x86_64/ptk/bin/connectomist"))
if args.verbose > 1:
    print("[result] In folder: {0}.".format(subjdir))
