"""Kraken - components.base module.

Classes:
Scene -- Scene root representation.

"""

import json

from kraken.core.maths import *
from kraken.core.objects import elements
from kraken.core.objects import layers


class BaseComponent(elements.SceneObject):
    """Base rigging component."""

    __kType__ = "Component"

    def __init__(self, name, side="M", parent=None):
        """Initializes Base component.

        Arguments:
        parent -- Object, object that is the parent of this component.

        """

        super(BaseComponent, self).__init__(name, parent)
        self.container = None
        self.guide = None
        self._side = None
        self.side = side
        self.sideScale = 1.0
        self.ctrlColor = "green"
        self.layers = {}
        self.spliceOps = {}
        self.definition = {
                           "layers":{},
                           "io":{}
                          }


    # ===================
    # Property Functions
    # ===================
    def getSide(self):
        return self._side


    def setSide(self, value):
        validSides = ["L","M","R"]
        if value not in validSides:
            raise ValueError("Invalid value for side! Valid sides: " + str(validSides))

        self._side = value

    side = property(getSide, setSide)


    # ================
    # Layer Functions
    # ================
    def addLayer(self, layerName):
        """Adds a layer to the component.

        Arguments:
        layerName -- String, name of the layer.

        Return:
        New layer.

        """

        newLayer = layers.Layer(layerName, self)
        self.layers[layerName] = newLayer

        return newLayer


    # ======================
    # Guide Build Functions
    # ======================
    def _preBuildGuide(self):
        """Pre-build operations.

        Return:
        True if successful.

        """

        return


    def _buildGuide(self):
        """Builds component in each DCC application.

        Implement in sub-classes.

        Return:
        True if successful.

        """

        return


    def _postBuildGuide(self):
        """Post-build operations.

        Return:
        True if successful.

        """

        return


    def buildGuide(self):
        """Method sequence to build the guide.

        Return:
        self.object3D

        """

        if self.guide is None:
            self._preBuildGuide()
            self._buildGuide()
            self._postBuildGuide()

        return self.guide


    # ================
    # Build Functions
    # ================
    def _preBuild(self):
        """Pre-build operations.

        Return:
        True if successful.

        """

        super(BaseComponent, self)._preBuild()

        if self.side == "R":
            self.sideScale = -1.0
            self.ctrlColor = "red"

        return True


    def buildDef(self):
        """Builds the Rig Definition and stores to definition attribute.

        Return:
        Dictionary of object data.
        """

        self.build()

        for eachLayer in self.layers:
            self.definition["layers"][eachLayer] = self.layers[eachLayer].buildDef()

        return self.definition