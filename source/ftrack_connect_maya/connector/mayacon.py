import os
import uuid
from ftrack_connect.connector import base as maincon
import maya.cmds as mc
import maya.OpenMayaUI as mui
import maya.mel as mm

from ftrack_connect.connector import FTAssetHandlerInstance


class DockedWidget(object):
    def __init__(self, widget):
        super(DockedWidget, self).__init__()
        self.panelWidth = 650
        self.qtObject = widget
        self.dockAt = 'right'
        self.dockName = 'myDock'
        self.type = 'panel'
        self.dockAllowedAreas = ['all']
        self.gotRefresh = None

    # Attach QT Gui to application
    def show(self):
        has_name = hasattr(self.qtObject, 'dockControlName')
        if has_name:
            name = self.qtObject.dockControlName
            mc.dockControl(name, e=True, r=True)
            if not mc.dockControl(
                name, q=True, io=True
            ):
                returnObj = self.qtObject
            else:
                self.createDockLayout()
                returnObj = self.qtObject

            if self.gotRefresh:
                returnObj.refresh()
            return returnObj

        self.qtObject.show()
        self.createDockLayout()
        return self.qtObject

    def getWindow(self):
        return self.qtObject

    def createDockLayout(self):
        gMainWindow = mm.eval('$temp1=$gMainWindow')
        columnLay = mc.paneLayout(parent=gMainWindow, width=200)
        dockControl = mc.dockControl(
            l=self.qtObject.windowTitle().replace('ftrack', ''),
            allowedArea="all",
            area="right",
            content=columnLay,
            width=self.panelWidth
        )
        mc.control(str(self.qtObject.objectName()), e=True, p=columnLay)
        self.qtObject.dockControlName = dockControl
        return


class Connector(maincon.Connector):
    def __init__(self):
        super(Connector, self).__init__()

    @staticmethod
    def getAssets():
        allObjects = mc.ls(type='ftrackAssetNode')

        componentIds = []

        for ftrackobj in allObjects:
            if not mc.referenceQuery(ftrackobj, isNodeReferenced=True):
                assetcomponentid = mc.getAttr(ftrackobj + ".assetComponentId")
                try:
                    nameInScene = mc.connectionInfo(
                        ftrackobj + ".assetLink",
                        destinationFromSource=True
                    )
                    nameInScene = nameInScene[0].split(".")[0]
                except:
                    print 'AssetLink broken for assetNode ' + str(ftrackobj)
                    continue

                componentIds.append((assetcomponentid, nameInScene))
        return componentIds

    @staticmethod
    def getFileName():
        return mc.file(query=1, sceneName=True)

    @staticmethod
    def getMainWindow():
        ptr = mui.MQtUtil.mainWindow()
        if ptr is not None:
            import shiboken
            from PySide import QtGui
            return shiboken.wrapInstance(long(ptr), QtGui.QMainWindow)

    @staticmethod
    def wrapinstance(ptr, base=None):
        import shiboken
        from PySide import QtGui, QtCore

        """
        Utility to convert a pointer to a Qt class instance (PySide/PyQt compatible)

        :param ptr: Pointer to QObject in memory
        :type ptr: long or Swig instance
        :param base: (Optional) Base class to wrap with (Defaults to QObject, which should handle anything)
        :type base: QtGui.QWidget
        :return: QWidget or subclass instance
        :rtype: QtGui.QWidget
        """
        if ptr is None:
            return None
        ptr = long(ptr)  # Ensure type
        if 'shiboken' in globals():
            if base is None:
                qObj = shiboken.wrapInstance(long(ptr), QtCore.QObject)
                metaObj = qObj.metaObject()
                cls = metaObj.className()
                superCls = metaObj.superClass().className()
                if hasattr(QtGui, cls):
                    base = getattr(QtGui, cls)
                elif hasattr(QtGui, superCls):
                    base = getattr(QtGui, superCls)
                else:
                    base = QtGui.QWidget
            return shiboken.wrapInstance(long(ptr), base)
        else:
            return None

    @staticmethod
    def importAsset(iAObj):
        iAObj.assetName = "_".join(
            [iAObj.assetType.upper(), iAObj.assetName, "AST"]
        )
        # Maya converts - to _ so let's do that as well
        iAObj.assetName = iAObj.assetName.replace('-', '_')

        # Check if this AssetName already exists in scene
        iAObj.assetName = Connector.getUniqueSceneName(iAObj.assetName)

        assetHandler = FTAssetHandlerInstance.instance()
        importAsset = assetHandler.getAssetClass(iAObj.assetType)
        if importAsset:
            result = importAsset.importAsset(iAObj)
            return result
        else:
            return 'assetType not supported'

    @staticmethod
    def selectObject(applicationObject=''):
        mc.select(applicationObject, r=True)

    @staticmethod
    def selectObjects(selection):
        mc.select(selection)

    @staticmethod
    def removeObject(applicationObject=''):
        ftrackNode = mc.listConnections(
            applicationObject + '.ftrack', d=False, s=True
        )
        ftrackNode = ftrackNode[0]
        assetComponent = mc.getAttr(ftrackNode + ".assetTake")
        assetType = mc.getAttr(ftrackNode + ".assetType")

        removeReference = True
        if assetComponent == 'alembic':
            removeReference = False

        if assetType == 'anim' and assetComponent == 'mayamc':
            removeReference = False

        if removeReference:
            referenceNode = Connector.getReferenceNode(applicationObject)
            if referenceNode:
                mc.file(rfn=referenceNode, rr=True)
        try:
            mc.delete(applicationObject)  # remove group
        except:
            print 'Asset or grp already deleted'

    @staticmethod
    def changeVersion(applicationObject=None, iAObj=None):
        assetHandler = FTAssetHandlerInstance.instance()
        changeAsset = assetHandler.getAssetClass(iAObj.assetType)
        if changeAsset:
            result = changeAsset.changeVersion(iAObj, applicationObject)
            return result
        else:
            print 'assetType not supported'
            return False

    @staticmethod
    def getSelectedObjects():
        return mc.ls(selection=True)

    @staticmethod
    def getSelectedAssets():
        selection = mc.ls(selection=True)
        selectedObjects = []
        for node in selection:
            try:
                mc.listConnections(node + '.ftrack', d=False, s=True)
                selectedObjects.append(node)
            except:
                transformParents = mc.listRelatives(
                    node, allParents=True, type='transform'
                )
                for parent in transformParents:
                    try:
                        mc.listConnections(parent + '.ftrack', d=False, s=True)
                        selectedObjects.append(parent)
                        break
                    except:
                        pass

        return selectedObjects

    @staticmethod
    def setNodeColor(applicationObject='', latest=True):
        pass

    @staticmethod
    def publishAsset(iAObj=None):
        assetHandler = FTAssetHandlerInstance.instance()
        pubAsset = assetHandler.getAssetClass(iAObj.assetType)
        if pubAsset:
            publishedComponents, message = pubAsset.publishAsset(iAObj)
            return publishedComponents, message
        else:
            return [], 'assetType not supported'

    @staticmethod
    def getConnectorName():
        return 'maya'

    @staticmethod
    def getUniqueSceneName(assetName):
        currentSelection = mc.ls(sl=True)
        try:
            mc.select(assetName)
            uniqueNameNotFound = True
            i = 0
            while uniqueNameNotFound:
                uniqueAssetName = assetName + str(i)
                try:
                    mc.select(uniqueAssetName)
                except:
                    uniqueNameNotFound = False
                i = i + 1

        except:
            uniqueAssetName = assetName
        if len(currentSelection) > 0:
            mc.select(currentSelection)
        return uniqueAssetName

    @staticmethod
    def getReferenceNode(assetLink):
        res = ''
        try:
            res = mc.referenceQuery(assetLink, referenceNode=True)
        except:
            childs = mc.listRelatives(assetLink, children=True)

            if childs:
                for child in childs:
                    try:
                        res = mc.referenceQuery(child, referenceNode=True)
                        break

                    except:
                        pass
            else:
                return None
        if res == '':
            print 'Could not find reference node'
            return None
        else:
            return res

    @staticmethod
    def takeScreenshot():
        import tempfile
        nodes = mc.ls(sl=True)
        mc.select(cl=True)

        # Ensure JPEG is set in renderglobals.
        # Only used on windows for some reason
        currentFormatStr = mc.getAttr(
            'defaultRenderGlobals.imageFormat',
            asString=True
        )

        restoreRenderGlobals = False
        if not (
            'jpg' in currentFormatStr.lower() or
            'jpeg' in currentFormatStr.lower()
        ):
            currentFormatInt = mc.getAttr('defaultRenderGlobals.imageFormat')
            mc.setAttr('defaultRenderGlobals.imageFormat', 8)
            restoreRenderGlobals = True

        filename = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
        res = mc.playblast(
            format="image",
            frame=mc.currentTime(query=True),
            compression='jpg',
            quality=80,
            showOrnaments=False,
            forceOverwrite=True,
            viewer=False,
            filename=filename
        )

        if restoreRenderGlobals:
            mc.setAttr('defaultRenderGlobals.imageFormat', currentFormatInt)

        if nodes is not None and len(nodes):
            mc.select(nodes)
        res = res.replace('####', '*')
        import glob
        path = glob.glob(res)[0]
        return path

    @staticmethod
    def batch():
        return mc.about(batch=True)

    @classmethod
    def registerAssets(cls):
        import mayaassets
        mayaassets.registerAssetTypes()
        super(Connector, cls).registerAssets()

    @staticmethod
    def executeInThread(function, arg):
        import maya.utils
        maya.utils.executeInMainThreadWithResult(function, arg)

    # Make certain scene validations before actualy publishing
    @classmethod
    def prePublish(cls, iAObj):
        result, message = super(Connector, cls).prePublish(iAObj)
        if not result:
            return result, message
        nodes = mc.ls(sl=True)
        if len(nodes) == 0:
            if 'exportMode' in iAObj.options and (iAObj.options['exportMode'] == 'Selection'):
                return None, 'Nothing selected'
            if 'alembicExportMode' in iAObj.options and (iAObj.options['alembicExportMode'] == 'Selection'):
                return None, 'Nothing selected'

        return True, ''
