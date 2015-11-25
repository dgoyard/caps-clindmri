#! /usr/bin/env python
##########################################################################
# NSAP - Copyright (C) CEA, 2013-2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import print_function
import nibabel.gifti.giftiio as gio
import os

# Clindmri import
import clindmri.plot.pvtk as pvtk
from clindmri.extensions.freesurfer.reader import TriSurface


class LabelsOnPick(object):
    """ Create a picker callback to display some labels.
    """
    def __init__(self, textactor, picker=None, actors=None,
                 static_position=True, to_keep_actors=None):
        """ Initialize the LabelsOnPick class.

        Parameters
        ----------
        textactor: vtkActor (mandatory)
            an actor with a text mapper.
        picker: vtkPropPicker (optional, default None)
            a picker.
        actors: vtkActor (optional, default None)
            all the actors to interact with.
        static_position: bool (optional, default True)
            if True the text labels will be displayed on the lower left corner,
            otherwise at the picked object position.
        to_keep_actors: list (optional, default None)
            a list of actor labels to keep visibile when an object is picked.
        """
        self.textactor = textactor
        self.textmapper = textactor.GetMapper()
        self.picker = picker
        self.actors = None
        self.static_position = static_position
        self.to_keep_actors = to_keep_actors or []

    def __call__(self, obj, event):    
        """ When an actor is picked, display its label and focus on this
        actor only.
        """
        # Pick an actor
        actor = self.picker.GetProp3D()

        # Restore all actors visibilities
        if actor is None:
            for act in self.actors:
                act.SetVisibility(True)
            self.textactor.VisibilityOff()
        # Focus on the picked actor and display the fold label
        else:
            for act in self.actors:
                if act.label not in self.to_keep_actors:
                    act.SetVisibility(False)
            actor.SetVisibility(True)
            self.textmapper.SetInput("Fold: {0}".format(actor.label))
            self.textactor.VisibilityOn()
            if not self.static_position:
                point = self.picker.GetSelectionPoint()
                self.textactor.SetPosition(point[:2])


def display_folds(folds_file, labels, weights, white_file=None,
                  interactive=True, snap=False, animate=False, outdir=None,
                  name="folds", actor_ang=(0., 0., 0.)):
    """ Display the folds computed by morphologist.

    The scene supports one feature activated via the keystroke:

    * 'p': Pick the data at the current mouse point. This will pop-up a window
      with information on the current pick (ie. the fold name). 

    Parameters
    ----------
    folds_file: str( mandatory)
        the folds '.gii' file.
    labels: dict (mandatory)
        a mapping between a mesh id and its label.
    weights: dict (mandatory)
        a mapping between a mesh label and its wheight in [0, 1].
    white_file: str (optional, default None)
        if specified the white surface will be displayed.
    interactive: bool (optional, default True)
        if True display the renderer.
    snap: bool (optional, default False)
        if True create a snap of the scene: need a valid outdir.
    animate: bool (optional, default False)
        if True create a gif 360 degrees animation of the scene: need a valid
        outdir.
    outdir: str (optional, default None)
        an existing directory.
    name: str (optional, default 'folds')
        the basename of the generated files.
    actor_ang: 3-uplet (optinal, default (0, 0, 0))
        the actors x, y, z position (in degrees).
    """
    # Load the folds file
    image = gio.read(folds_file)
    nb_of_surfs = len(image.darrays)
    if nb_of_surfs % 2 != 0:
        raise ValueError("Need an odd number of arrays (vertices, triangles).")

    # Create an actor for each fold
    ren = pvtk.ren()
    ren.SetBackground(1, 1, 1)
    for vertindex in range(0, nb_of_surfs, 2):
        vectices = image.darrays[vertindex].data
        triangles = image.darrays[vertindex + 1].data
        labelindex = image.darrays[vertindex].get_metadata()["Timestep"]
        if labelindex != image.darrays[vertindex + 1].get_metadata()["Timestep"]:
            raise ValueError("Gifti arrays '{0}' and '{1}' do not share the "
                             "same label.".format(vertindex, vertindex + 1))
        labelindex = int(labelindex)
        if labelindex in labels:
            label = labels[labelindex]
            if label in weights:
                weight = weights[label] * 256.
            else:
                weight = 0
        else:
            label = "NC"
            weight = 0
        surf = TriSurface(vectices, triangles, labels=None)
        actor = pvtk.surface(surf.vertices, surf.triangles,
                             surf.labels + weight)
        actor.label = label
        actor.RotateX(actor_ang[0])
        actor.RotateY(actor_ang[1])
        actor.RotateZ(actor_ang[2])
        pvtk.add(ren, actor)

    # Add the white surface if specified
    if white_file is not None:
        image = gio.read(white_file)
        nb_of_surfs = len(image.darrays)
        if nb_of_surfs != 2:
            raise ValueError("'{0}' does not a contain a valid white "
                             "mesh.".format(white_file))
        vectices = image.darrays[0].data
        triangles = image.darrays[1].data
        surf = TriSurface(vectices, triangles, labels=None)
        actor = pvtk.surface(surf.vertices, surf.triangles, surf.labels,
                             opacity=1, set_lut=False)
        actor.label = "white"
        actor.RotateX(actor_ang[0])
        actor.RotateY(actor_ang[1])
        actor.RotateZ(actor_ang[2])
        pvtk.add(ren, actor)

    # Show the renderer
    if interactive:
        actor = pvtk.text("!!!!", font_size=15, position=(10, 10),
                          is_visible=False)
        pvtk.add(ren, actor)
        obs = LabelsOnPick(actor, static_position=True,
                           to_keep_actors=["white"])
        pvtk.show(ren, title="morphologist folds", observers=[obs])

    # Create a snap
    if snap:
        if not os.path.isdir(outdir):
            raise ValueError("'{0}' is not a valid directory.".format(outdir))
        pvtk.record(ren, outdir, name, n_frames=1)

    # Create an animation
    if animate:
        if not os.path.isdir(outdir):
            raise ValueError("'{0}' is not a valid directory.".format(outdir))
        pvtk.record(ren, outdir, name, n_frames=36, az_ang=10, animate=True,
                    delay=25)


def parse_graph(graph_file):
    """ Parse a Morphologist graph file to get the fold labels.

    Parameters
    ----------
    graph_file: str (mandatory)
        the path to a morphologist '.arg' graph file.

    Returns
    -------
    labels: dict
        a mapping between a mesh id and its label.
    """
    # Read all the lines in the graph file
    with open(graph_file) as open_file:
        lines = open_file.readlines()

    # Search labels
    infold = False
    labels = {}
    for line in lines:

        # Locate fold items
        if line.startswith("*BEGIN NODE fold"):
            infold = True
            continue
        if infold and line.startswith("*END"):
            if meshid in labels:
                raise ValueError("'{0}' mesh id already found.".format(meshid))
            labels[meshid] = label
            infold = False
            continue

        # In fold item detect the mesh id and the associated label
        if infold and line.startswith("label"):
            label = line.replace("label", "").strip()
        if infold and line.startswith("Tmtktri_label"):
            meshid = int(line.replace("Tmtktri_label", "").strip())

    return labels
            

