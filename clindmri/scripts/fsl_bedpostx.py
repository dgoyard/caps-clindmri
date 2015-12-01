#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# python modules
import os
import glob
import numpy
import shutil
import argparse

# bredala module
try:
    import bredala
    bredala.USE_PROFILER = False
    bredala.register("clindmri.segmentation.fsl", names=["bet2"])
    bredala.register("clindmri.tractography.fsl",
                     names=["bedpostx", "bedpostx_datacheck"])
    bredala.register("clindmri.registration.utils", names=["extract_image"])
    bredala.register("clindmri.plot.slicer", names=["plot_image"])
except:
    pass

# clindmri modules
from clindmri.segmentation.fsl import bet2
from clindmri.plot.slicer import plot_image
from clindmri.tractography.fsl import bedpostx
from clindmri.registration.utils import extract_image
from clindmri.tractography.fsl import bedpostx_datacheck


# parameters to keep trace
__hopla__ = [
    "subjectid", "diffusion_file", "mask_file", "bvecs_file", "bvals_file",
    "b0_file", "b0_brain_file", "bedpostx_outdir", "merged_files"]


doc = """
FSL Bedpostx
~~~~~~~~~~~~

Performs a parametric deconvolution of the diffusion signal to fibre
orientations.

**Steps**

1 - Obtain what is brain and what isn't using BET on the corrected b0 data.
2 - Estimate fibre orientations using FSL Bedpostx model-based deconvolution.

**Input files**

- The *.bval files contain a scalar value for each applied gradient,
  corresponding to the respective b-value.
- The *.bvec files contain a 3x1 vector for each gradient, indicating the
  gradient direction.
- The diffuson dta: ith volume in the data corresponds to a measurement
  obtained after applying a diffusion-sensitising gradient with a b-value given
  by th ith entry in *.bval and a gradient direction given by the ith vector in
  *.bvec

**Command**

python $HOME/git/clindmri/scripts/fsl_bedpostx.py
    -v 2
    -c /i2bm/local/fsl-5.0.9/etc/fslconf/fsl.sh
    -f /volatile/imagen/dmritest/001/raw/hardi-b1500-1-001.nii.gz
    -g /volatile/imagen/dmritest/001/raw/hardi-b1500-1-001.bvec
    -b /volatile/imagen/dmritest/001/raw/hardi-b1500-1-001.bval
    -d /volatile/imagen/dmritest/fsl
    -s 000043561374
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
    "-c", "--config", dest="fslconfig", metavar="FILE", required=True,
    help="the FSL configuration file.", type=is_file)
parser.add_argument(
    "-f", "--diffusionfile", dest="diffusion_file", metavar="FILE",
    required=True,
    help="the diffusion data after correction for distorsions.", type=is_file)
parser.add_argument(
    "-g", "--bvecsfile", dest="bvecs_file", metavar="FILE", required=True,
    help="the *.bvec files contain a 3x1 vector for each gradient, "
         "indicating the gradient direction.", type=is_file)
parser.add_argument(
    "-b", "--bvalsfile", dest="bvals_file", metavar="FILE", required=True,
    help="the *.bval files contain a scalar value for each applied gradient, "
         "corresponding to the respective b-value.", type=is_file)
parser.add_argument(
    "-d", "--fsldir", dest="fsldir", required=True, metavar="PATH",
    help="the FSL processing home directory.", type=is_directory)
parser.add_argument(
    "-s", "--subjectid", dest="subjectid", required=True,
    help="the subject identifier.")
args = parser.parse_args()


"""
First check if the subject FSL directory exists on the file system, and
clean it if requested.
"""
if args.verbose > 0:
    print("[info] Start FSL bedpostx ...")
    print("[info] Directory: {0}.".format(args.fsldir))
    print("[info] Subject: {0}.".format(args.subjectid))
    print("[info] Diffusion data: {0}.".format(args.diffusion_file))


subjdir = os.path.join(args.fsldir, args.subjectid)
# clean the subject directory
if os.path.isdir(subjdir) and args.erase:
    shutil.rmtree(subjdir)
# create the subject directory
if not os.path.isdir(subjdir):
    os.makedirs(subjdir)

"""
Diffusion Processing
====================

At this point we have a motion- & artifact-corrected image, the corrected
gradient table.

From our DTI data, we need to produce the mask of the non-diffusion-weighted
image.

Non-diffusion-weighted mask
---------------------------

We need to generate a mask on which the model is estimated. We first select the
first non-diffusion weighted volume of the DTI sequence and then use 'bet2' on
this image with a fractional intensity threshold of 0.25 (this is generally a
robust threshold to remove unwanted tissue from a non-diffusion weighted image)
and the 'm' option that creates a binary 'nodif_brain_mask' image.
"""

# get the b0 file
bvals = numpy.loadtxt(args.bvals_file).tolist()
b0_index = bvals.index(0)
b0_file = os.path.join(subjdir, "nodif.nii.gz")
if not os.path.isfile(b0_file):
    extract_image(
        args.diffusion_file,
        index=b0_index,
        out_file=b0_file)

# Get the qc output directory
qcdir = os.path.join(subjdir, "qc")
if not os.path.isdir(qcdir):
    os.makedirs(qcdir)

# create a pdf snap of the b0 image
snap_file = os.path.join(qcdir, "nodif.pdf")
plot_image(b0_file, snap_file=snap_file, name="nodif")

# generate a brain mask on the corrected b0 data
b0_brain_file = os.path.join(subjdir, "nodif_brain")
bet_files = glob.glob(b0_brain_file + "*")
if len(bet_files) == 0:
    (output, mask_file, mesh_file, outline_file,
     inskull_mask_file, inskull_mesh_file,
     outskull_mask_file, outskull_mesh_file, outskin_mask_file,
     outskin_mesh_file, skull_mask_file) = bet2(
        b0_file,
        b0_brain_file,
        m=True,
        f=0.25)
else:
    mask_file = sorted(bet_files)[0]
    if not os.path.isfile(mask_file):
        raise IOError("FileDoesNotExist: '{0}'.".format(mask_file))

# create a pdf snap of the brain mask
snap_file = os.path.join(qcdir, "bet.pdf")
plot_image(b0_file, contour_file=mask_file, snap_file=snap_file, name="bet")


"""
Generating PDFs
---------------

We use 'bedpostx' to generate PDFs of the diffusion direction. 'bedpostx' takes
about 5 hours of compute time. This routine need specific files that are
checked with the 'bedpostx_datacheck' command.
"""

# copy all necessary files in the same repertory for the bedpostx execution
bedpostx_indir = os.path.join(subjdir, "diffusion")
bedpostx_outdir = os.path.join(subjdir, "diffusion.bedpostX")
if not os.path.isdir(bedpostx_indir):
    os.mkdir(bedpostx_indir)
if len(os.listdir(bedpostx_outdir)) == 0:
    shutil.copy2(mask_file, bedpostx_indir)
    data_ext = ".".join(args.diffusion_file.split(".")[1:])
    shutil.copy2(args.diffusion_file, os.path.join(
                 bedpostx_indir, "data." + data_ext))
    shutil.copy2(args.bvecs_file, os.path.join(bedpostx_indir, "bvecs"))
    shutil.copy2(args.bvals_file, os.path.join(bedpostx_indir, "bvals"))
    if not bedpostx_datacheck(bedpostx_indir):
        raise IOError("'{0}' does not contain the data expected by "
                      "'bedpostx'.".format(bedpostx_indir))

    # execute bedpostx
    (bedpostx_outdir, merged_th, merged_ph,
     merged_f, mean_th, mean_ph,
     mean_f, dyads) = bedpostx(
        bedpostx_indir)
else:
    merged_files = glob.glob(os.path.join(bedpostx_outdir, "merged*"))
    if len(merged_files) == 0:
        raise IOError("FilesDoNotExist: in '{0}'.".format(bedpostx_outdir))
