"""Kraken - objects.object_3d module.

Classes:
Object3D - Base Object3D Object.

"""

from kraken.core.configs.config import Config
from kraken.core.objects.scene_item import SceneItem
from kraken.core.maths.xfo import Xfo
from kraken.core.maths.rotation_order import RotationOrder
from kraken.core.objects.attributes.attribute_group import AttributeGroup


class Object3D(SceneItem):
    """Kraken base object type for any 3D object."""

    def __init__(self, name, parent=None):
        super(Object3D, self).__init__(name, parent)
        self._component = None
        self._children = []
        self._flags = {}
        self._attributeGroups = []
        self._constraints = []
        self._xfo = Xfo()
        self._ro = RotationOrder()
        self._color = None
        self._visibility = True
        self._shapeVisibility = True

        if parent is not None:
            parent.addChild(self)


    # ==================
    # Property Methods
    # ==================
    @property
    def xfo(self):
        """Gets xfo property of this Object3D.

        Return:
        Scalar, xfo property of this Object3D.

        """

        return self._xfo


    @xfo.setter
    def xfo(self, value):
        """Sets xfo of this Object3D.

        Note: In Python, objects are always referenced, meaning to get a unique
        instance, an explicit clone is required. In KL, structs are passed by
        value, meaning that every assignment of a struct causes a clone.

        This means that in KL it is impossible for 2 objects to reference the
        same KL math object. This is an important performance feature of KL.

        The members of the KL Math objects have this property. 2 Xfos cannot
        share the same tr value. Here we implcitly clone the math object to
        ensure the same behavior as in KL.

        Arguments:
        value -- Xfo, vector to set the xfo by.

        Return:
        True if successful.

        """

        self._xfo = value.clone()

        return True


    @property
    def ro(self):
        """Gets Rotation Order property of this Object3D.

        Return:
        Scalar, Rotation Order property of this Object3D.

        """

        return self._ro


    @ro.setter
    def ro(self, value):
        """Sets Rotation Order of this Object3D.

        Note: In Python, objects are always referenced, meaning to get a unique
        instance, an explicit clone is required. In KL, structs are passed by
        value, meaning that every assignment of a struct causes a clone.

        This means that in KL it is impossible for 2 objects to reference the
        same KL math object. This is an important performance feature of KL.

        The members of the KL Math objects have this property. 2 Xfos cannot
        share the same tr value. Here we implcitly clone the math object to
        ensure the same behavior as in KL.

        Arguments:
        value -- RotationOrder, new rotation order.

        Return:
        True if successful.

        """

        self._ro = value.clone()

        return True



    # =============
    # Name Methods
    # =============
    def getDecoratedPath(self):
        """Gets the decorated path of the object.

        Return:
        String, decorated path  of the object.

        """

        if self.getParent() is not None and not self.getParent().isTypeOf('Component'):
            return self.getParent().getDecoratedPath() + '.' + self.getBuildName()

        return self.getBuildName()


    def getBuildName(self):
        """Returns the build name for the object.

        Return:
        String, name to be used in the DCC.

        """

        typeNameHierarchy = self.getTypeHierarchyNames()

        config = Config.getInstance()

        # If flag is set on object to use explicit name, return it.
        if config.getExplicitNaming() is True or self.testFlag('EXPLICIT_NAME'):
            return self.getName()

        nameTemplate = config.getNameTemplate()

        # Get the token list for this type of object
        format = None
        for typeName in nameTemplate['formats'].keys():
            if typeName in typeNameHierarchy:
                format = nameTemplate['formats'][typeName]
                break

        if format is None:
            format = nameTemplate['formats']['default']

        objectType = None
        for eachType in typeNameHierarchy:
            if eachType in nameTemplate['types'].keys():
                objectType = eachType
                break

        if objectType is None:
            objectType = 'default'

        # Generate a name by concatenating the resolved tokens together.
        builtName = ""
        skipSep = False
        for token in format:

            if token is 'sep':
                if not skipSep:
                    builtName += nameTemplate['separator']

            elif token is 'location':
                if self.isTypeOf('Component'):
                    location = self.getLocation()
                else:
                    location = self.getComponent().getLocation()

                if location not in nameTemplate['locations']:
                    raise ValueError("Invalid location on: " + self.getFullName())

                builtName += location

            elif token is 'type':

                if objectType == 'Locator' and self.testFlag('inputObject'):
                    objectType = 'ComponentInput'
                elif objectType == 'Locator' and self.testFlag('outputObject'):
                    objectType = 'ComponentOutput'

                builtName += nameTemplate['types'][objectType]

            elif token is 'name':
                builtName += self.getName()

            elif token is 'component':
                if self.getComponent() is None:
                    skipSep = True
                    continue
                builtName += self.getComponent().getName()

            elif token is 'container':
                if self.getContainer() is None:
                    skipSep = True
                    continue
                builtName += self.getContainer().getName()

            else:
                raise ValueError("Unresolvabled token '" + token + "' used on: " + self.getFullName())

        return builtName


    # ==================
    # Hierarchy Methods
    # ==================
    def getContainer(self):
        """Returns the Container the object belongs to.

        Return:
        Object, Container.

        """

        parent = self.getParent()
        while (parent is not None and 'Container' not in parent.getTypeHierarchyNames()):
            parent = parent.getParent()

        return parent


    def getLayer(self):
        """Returns the Layer the object belongs to.

        Return:
        Object, Layer this object belongs to.

        """

        parent = self.getParent()
        while (parent is not None and not parent.isTypeOf('Layer')):
            parent = parent.getParent()

        return parent


    # ==================
    # Component Methods
    # ==================
    def getComponent(self):
        """Returns the component of the object as an object.

        Return:
        Component of this object.

        """

        return self._component


    def setComponent(self, component):
        """Sets the component attribute of this object.

        Arguments:
        component -- Object, object that is the component of this one.

        Return:
        True if successful.

        """

        self._component = component

        return True


    # ==============
    # Child Methods
    # ==============
    def checkChildIndex(self, index):
        """Checks the supplied index is valid.

        Arguments:
        index -- Integer, child index to check.

        """

        if index > len(self.getChildren()):
            raise IndexError("'" + str(index) + "' is out of the range of the 'children' array.")

        return True


    def addChild(self, child):
        """Adds a child to this object.

        We allow for duplicate child names as long as the types differ.

        Arguments:
        child -- Object, object that will be a child of this object.

        Return:
        True if successful.

        """

        # foundChild = self.findChild(child.getName(), childType=child.getTypeName())
        # if foundChild is not None:
        #     raise Exception("Child with the same name already exists: '" +
        #                     child.getName() + "'")

        if child.getParent() is not None:
            parent = child.getParent()
            if child in parent.getChildren():
                parent.getChildren().remove(child)

        self.getChildren().append(child)
        child.setParent(self)

        # Assign the child the same component.
        if self._component is not None:
            child.setComponent(self._component)

        return True


    def removeChildByIndex(self, index):
        """Removes a child from this object by index.

        Arguments:
        index -- Integer, index of child to remove.

        Return:
        True if successful.

        """

        if self.checkChildIndex(index) is not True:
            return False

        del self.getChildren()[index]

        return True


    def removeChildByName(self, name):
        """Removes a child from this object by name.

        Arguments:
        name -- String, name of child to remove.

        Return:
        True if successful.

        """

        removeIndex = None

        for i, eachChild in enumerate(self.getChildren()):
            if eachChild.getName() == name:
                removeIndex = i

        if removeIndex is None:
            raise ValueError("'" + name + "' is not a valid child of this object.")

        self.removeChildByIndex(removeIndex)

        return True


    def getChildren(self):
        """Gets the children of this object.

        Return:
        List, child objects.

        """

        return self._children


    def getNumChildren(self):
        """Returns the number of children this object has.

        Return:
        Integer, number of children of this object.

        """

        return len(self.getChildren())


    def getChildByIndex(self, index):
        """Returns the child object at specified index.

        Arguments:
        index -- Integer, index of the child to find.

        Return:
        Child object at specified index.

        """

        if self.checkChildIndex(index) is not True:
            return False

        return self.getChildren()[index]


    def getChildByName(self, name):
        """Returns the child object with the specified name.

        Return:
        Object if found.
        None if not found.

        """

        for eachChild in self.getChildren():
            if eachChild.getName() == name:
                return eachChild

        return None


    def getChildrenByType(self, childType):
        """Returns all children that are of the specified type.

        Arguments:
        childType -- String, type of children to find.

        Return:
        Array of child objects of the specified type.
        None if no objects of specified type are found.

        """

        childrenOfType = []
        for eachChild in self.getChildren():
            if eachChild.isTypeOf(childType):
                childrenOfType.append(eachChild)

        return childrenOfType


    def findChild(self, name, childType=None, targetObj=None):
        """Finds a child by recursively searching the hierarhcy for a child with
        the given name.

        Arguments:
        name -- String, name of the child to find.
        childType -- String, type of object to find.
        targetObj -- Object, object to search under. Used for recursive searching.

        Return:
        Object, child if found.

        """

        foundChild = None

        if targetObj == None:
            targetObj = self

        # Build children
        for i in xrange(targetObj.getNumChildren()):
            child = targetObj.getChildByIndex(i)

            if child.getName() == name and child.getTypeName() == childType:
                foundChild = child
            else:
                foundChild = self.findChild(name, childType=childType, targetObj=child)

            if foundChild is not None:
                break

        return foundChild


    def findChildrenByType(self, childType, targetObj=None):
        """Finds a child by recursively searching the hierarhcy for a child with
        the given name.

        Arguments:
        childType -- String, type of children to find.
        targetObj -- Object, object to search under. Used for recursive searching.

        Return:
        List, children of the searched type if found.

        """

        childrenOfType = []

        self._findChildByType(childType, childrenOfType)

        return childrenOfType


    def _findChildByType(self, childType, foundArray, targetObj=None):
        """Protected find child by type method.

        Arguments:
        childType -- Class, type of children to find.
        foundArray -- List, list of found children to append to.
        targetObj -- Object, object to search under. Used for recursive searching.

        Return:
        True if successful.

        """

        if targetObj == None:
            targetObj = self

        # Build children
        for i in xrange(targetObj.getNumChildren()):
            child = targetObj.getChildByIndex(i)

            if type(child).__name__ is childType:
                foundArray.append(child)

            newFoundChildren = self._findChildByType(childType, foundArray, child)

        return


    # =============
    # Flag Methods
    # =============
    def setFlag(self, name):
        """Sets the flag of the specified name.

        Return:
        True if successful.

        """

        self._flags[name] = True

        return True


    def testFlag(self, name):
        """Tests if the specified flag is set.

        Arguments:
        name -- String, name of the flag to test.

        Return:
        True if flag is set, false otherwise.

        """

        if name in self._flags:
            return True

        return False


    def clearFlag(self, name):
        """Clears the flag of the specified name.

        Arguments:
        name -- String, name of the flag to clear.

        Return:
        True if successful.

        """

        if name in self._flags:
            del self._flags[name]
            return True

        return False


    # ========================
    # Attribute Group Methods
    # ========================
    def checkAttributeGroupIndex(self, index):
        """Checks the supplied index is valid.

        Arguments:
        index -- Integer, attribute index to check.

        Return:
        True if successful.

        """

        if index > len(self._attributeGroups):
            raise IndexError("'" + str(index) + "' is out of the range of 'attributeGroups' array.")

        return True


    def addAttributeGroup(self, attributeGroup):
        """Adds an attributeGroup to this object.

        Arguments:
        attributeGroup -- Object, Attribute Group object to add to this object.

        Return:
        True if successful.

        """

        if attributeGroup.getName() in [x.getName() for x in self._attributeGroups]:
            raise IndexError("Child with " + attributeGroup.getName() + " already exists as a attributeGroup.")

        self._attributeGroups.append(attributeGroup)
        attributeGroup.setParent(self)

        return True


    def removeAttributeGroupByIndex(self, index):
        """Removes attribute at specified index.

        Arguments:
        index -- Integer, index of attribute to remove.

        Return:
        True if successful.

        """

        if self.checkAttributeGroupIndex(index) is not True:
            return False

        del self._attributeGroups[index]

        return True


    def removeAttributeGroupByName(self, name):
        """Removes the attribute with the specified name.

        Arguments:
        name -- String, name of the attribute to remove.

        Return:
        True if successful.

        """

        removeIndex = None

        for i, eachAttributeGroup in enumerate(self._attributeGroups):
            if eachAttributeGroup.getName() == name:
                removeIndex = i

        if removeIndex is None:
            return False

        self.removeAttributeGroupByIndex(removeIndex)

        return True


    def getNumAttributeGroups(self):
        """Returns the number of attributeGroups as an integer.

        Return:
        Integer of the number of attributeGroups on this object.

        """

        return len(self._attributeGroups)


    def getAttributeGroupByIndex(self, index):
        """Returns the attribute at the specified index.

        Arguments:
        index -- Integer, index of the attribute to return.

        Return:
        AttributeGroup at the specified index.
        False if not a valid index.

        """

        if self.checkAttributeGroupIndex(index) is not True:
            return False

        return self._attributeGroups[index]


    def getAttributeGroupByName(self, name):
        """Return the attribute group with the specified name.

        Arguments:
        name -- String, name of the attribute group to return.

        Return:
        Attribute with the specified name.
        None if not found.

        """

        for eachAttributeGroup in self._attributeGroups:
            if eachAttributeGroup.getName() == name:
                return eachAttributeGroup

        return None


    # ===================
    # Constraint Methods
    # ===================
    def checkConstraintIndex(self, index):
        """Checks the supplied index is valid.

        Arguments:
        index -- Integer, constraint index to check.

        Return:
        True if successful.

        """

        if index > len(self._constraints):
            raise IndexError("'" + str(index) + "' is out of the range of 'constraints' array.")

        return True


    def addConstraint(self, constraint):
        """Adds an constraint to this object.

        Arguments:
        constraint -- Object, Constraint object to add to this object.

        Return:
        True if successful.

        """

        if constraint.getName() in [x.getName() for x in self._constraints]:
            raise IndexError("Constraint with name '" + constraint.getName() + "'' already exists as a constraint.")

        self._constraints.append(constraint)
        constraint.setParent(self)
        constraint.setConstrainee(self)

        return True


    def removeConstraintByIndex(self, index):
        """Removes constraint at specified index.

        Arguments:
        index -- Integer, index of constraint to remove.

        Return:
        True if successful.

        """

        if self.checkConstraintIndex(index) is not True:
            return False

        del self._constraints[index]

        return True


    def removeConstraintByName(self, name):
        """Removes the constraint with the specified name.

        Arguments:
        name -- String, name of the constraint to remove.

        Return:
        True if successful.

        """

        removeIndex = None

        for i, eachConstraint in enumerate(self._constraints):
            if eachConstraint.getName() == name:
                removeIndex = i

        if removeIndex is None:
            return False

        self.removeConstraintByIndex(removeIndex)

        return True


    def getNumConstraints(self):
        """Returns the number of constraints as an integer.

        Return:
        Integer of the number of constraints on this object.

        """

        return len(self._constraints)


    def getConstraintByIndex(self, index):
        """Returns the constraint at the specified index.

        Arguments:
        index -- Integer, index of the constraint to return.

        Return:
        Constraint at the specified index.
        False if not a valid index.

        """

        if self.checkConstraintIndex(index) is not True:
            return False

        return self._constraints[index]


    def getConstraintByName(self, name):
        """Return the constraint group with the specified name.

        Arguments:
        name -- String, name of the constraint group to return.

        Return:
        Attribute with the specified name.
        None if not found.

        """

        for eachConstraint in self._constraints:
            if eachConstraint.getName() == name:
                return eachConstraint

        return None


    # ===================
    # Visibility Methods
    # ===================
    def getVisibility(self):
        """Returns the visibility status of the scene item.

        Return:
        Boolean, visible or not.

        """

        return self._visibility


    def setVisibility(self, value):
        """Sets the visibility of the scene object.

        Arguments:
        value -- Boolean, value of the visibility of the object.

        Return:
        True if successful.

        """

        self._visibility = value

        return True


    def getShapeVisibility(self):
        """Returns the shape visibility status of the scene item.

        Return:
        Boolean, visible or not.

        """

        return self._shapeVisibility


    def setShapeVisibility(self, value):
        """Sets the shape visibility of the scene object.

        Arguments:
        value -- Boolean, value of the visibility of the object.

        Return:
        True if successful.

        """

        self._shapeVisibility = value

        return True


    # ================
    # Display Methods
    # ================
    def setColor(self, color):
        """Sets the color of this object.

        Arguments:
        color -- String, name of the color you wish to set.

        Return:
        True if successful.

        """

        self._color = color

        return True


    def getColor(self):
        """Returns the color of the object.

        Return:
        String, color of the object.

        """

        return self._color


    # ==========================
    # Parameter Locking Methods
    # ==========================
    def lockRotation(self, x=False, y=False, z=False):
        """Sets flags for locking rotation parameters.

        Arguments:
        x -- Boolean, lock x axis.
        y -- Boolean, lock y axis.
        z -- Boolean, lock z axis.

        Return:
        True if successful.

        """

        if x is True:
            self.setFlag("lockXRotation")

        if y is True:
            self.setFlag("lockYRotation")

        if z is True:
            self.setFlag("lockZRotation")

        return True


    def lockScale(self, x=False, y=False, z=False):
        """Sets flags for locking scale parameters.

        Arguments:
        x -- Boolean, lock x axis.
        y -- Boolean, lock y axis.
        z -- Boolean, lock z axis.

        Return:
        True if successful.

        """

        if x is True:
            self.setFlag("lockXScale")

        if y is True:
            self.setFlag("lockYScale")

        if z is True:
            self.setFlag("lockZScale")

        return True


    def lockTranslation(self, x=False, y=False, z=False):
        """Sets flags for locking translation parameters.

        Arguments:
        x -- Boolean, lock x axis.
        y -- Boolean, lock x axis.
        z -- Boolean, lock x axis.

        Return:
        True if successful.

        """

        if x is True:
            self.setFlag("lockXTranslation")

        if y is True:
            self.setFlag("lockYTranslation")

        if z is True:
            self.setFlag("lockZTranslation")

        return True


    # ====================
    # Persistence Methods
    # ====================
    def jsonEncode(self, saver):
        """Returns the data for this object encoded as a JSON hierarchy.

        Arguments:

        Return:
        A JSON structure containing the data for this Object3D.

        """

        classHierarchy = self.getTypeHierarchyNames()

        jsonData = {
            '__typeHierarchy__': classHierarchy,
            'name': self.getName(),
            'parent': None,
            'children': [],
            'flags': self._flags,
            'attributeGroups': [],
            'constraints': [],
            'xfo': self.xfo.jsonEncode(),
            'color': self.getColor(),
            'visibility': self._visibility,
            'shapeVisibility': self._shapeVisibility,
        }

        if self.getParent() is not None:
            jsonData['parent'] = self.getParent().getName()

        if self.getColor() is not None:
            jsonData['color'] = saver.encodeValue(self.getColor())

        for child in self.getChildren():
            jsonData['children'].append(child.jsonEncode(saver))

        for attrGroup in self._attributeGroups:
            jsonData['attributeGroups'].append(attrGroup.jsonEncode(saver))

        for constr in self._constraints:
            jsonData['constraints'].append(constr.jsonEncode(saver))

        return jsonData


    def jsonDecode(self, loader, jsonData):
        """Returns the color of the object.

        Return:
        True if decoding was successful

        """
        self._flags =  jsonData['flags']
        self.xfo =  loader.decodeValue(jsonData['xfo'])
        if 'color' in jsonData and jsonData['color'] is not None:
            self.setColor(loader.decodeValue(jsonData['color']))
        self._visibility =  jsonData['visibility']
        self._shapeVisibility =  jsonData['shapeVisibility']

        for child in jsonData['children']:
            self.addChild(loader.construct(child))

        for attrGroup in jsonData['attributeGroups']:
            # There is one default attribute group assigned to each scene item.
            # Load data into the existing item instead of constructing a new one.
            if attrGroup['name'] == '':
                loader.registerItem(self._attributeGroups[0])
                self._attributeGroups[0].jsonDecode(loader, attrGroup)
            else:
                self.addAttributeGroup(loader.construct(attrGroup))

        for constr in jsonData['constraints']:
            self.addConstraint(loader.construct(constr))

        return True
