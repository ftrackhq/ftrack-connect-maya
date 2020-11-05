# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import copy
import sys

import maya.cmds as mc
import maya.mel as mel

import ftrack

import mayacon

from ftrack_connector_legacy.connector import (
    FTAssetHandlerInstance,
    HelpFunctions,
    FTAssetType,
    FTComponent
)

currentStartFrame = mc.playbackOptions(min=True, q=True)
currentEndFrame = mc.playbackOptions(max=True, q=True)


if mayacon.Connector.batch() is False:
    from ftrack_connector_legacy.connector import panelcom

SUPPORTED_SOUND_FORMATS = ['.aiff', '.wav']
if sys.platform == 'darwin':
    SUPPORTED_SOUND_FORMATS.append('.mp3')


class GenericAsset(FTAssetType):
    def __init__(self):
        super(GenericAsset, self).__init__()
        self.importAssetBool = False
        self.referenceAssetBool = False

    def importAsset(self, iAObj=None):
        '''Import asset defined in *iAObj*'''

        namespace = self._determineNameSpace(iAObj)

        if (
            iAObj.componentName == 'alembic' or
            iAObj.filePath.endswith('abc')
        ):
            try:
                mc.loadPlugin('AbcImport.so', qt=1)
            except:
                return 'Failed to load alembic plugin'

            self.oldData = set(mc.ls())

            if iAObj.options['importMode'] == 'Import':
                mc.createNode('transform', n=iAObj.assetName)
                mc.AbcImport(
                    iAObj.filePath,
                    mode='import',
                    reparent=iAObj.assetName
                )

            if iAObj.options['importMode'] == 'Reference':
                mc.file(
                    iAObj.filePath,
                    r=True,
                    type="Alembic",
                    ignoreVersion=True,
                    gl=False,
                    dr=False,
                    namespace=namespace,
                    mergeNamespacesOnClash=False
                )

            self.newData = set(mc.ls())

            self.linkToFtrackNode(iAObj)
        elif any(
                [iAObj.filePath.endswith(format) for format in SUPPORTED_SOUND_FORMATS]
                ):

            self.oldData = set(mc.ls())

            start_frame = mc.playbackOptions(q=True, min=True)
            mc.sound(file=iAObj.filePath, offset=start_frame)

            self.newData = set(mc.ls())

            self.linkToFtrackNode(iAObj)
        else:
            component = ftrack.Component(iAObj.componentId)
            groupReferenceBool = True
            self.importAssetBool = False
            kwargs = {
                'mergeNamespacesOnClash': True,
            }
            preserveReferences = True
            self.referenceAssetBool = True

            # Determine namespace
            kwargs['namespace'] = namespace

            # Determine import type
            mapping = {'.ma': 'mayaAscii', '.mb': 'mayaBinary'}
            importType = mapping.get(component.getFileType(), 'mayaBinary')

            if iAObj.componentName in [
                'mayaBinary', 'main', 'mayaBinaryScene',
                'mayaAscii', 'mayaAsciiScene'
            ]:
                if 'importMode' in iAObj.options:
                    if iAObj.options['importMode'] == 'Import':
                        self.importAssetBool = True
                        self.referenceAssetBool = False
                        # do not group when importing
                        groupReferenceBool = False
                    elif iAObj.options['importMode'] == 'Open':
                        self.importAssetBool = False
                        self.referenceAssetBool = False
                        # do not group when importing
                        groupReferenceBool = False
                        kwargs['open'] = True
                        kwargs.pop('mergeNamespacesOnClash', None)
                        kwargs.pop('namespace', None)

                if iAObj.componentName in ('mayaAscii', 'mayaAsciiScene'):
                    importType = 'mayaAscii'

            elif iAObj.componentName in ['audio']:
                importType = 'audio'
                self.importAssetBool = True
                self.referenceAssetBool = False

            if (iAObj.componentName in ['mayaBinaryScene'] or
                    kwargs.get('open', False)):
                confirmDialog = mc.confirmDialog(
                    title='Confirm',
                    message='Replace current scene?',
                    button=['Yes', 'No'],
                    defaultButton='No',
                    cancelButton='No',
                    dismissString='No'
                )
                if confirmDialog == 'Yes':
                    mc.file(new=True, force=True)
                else:
                    raise RuntimeWarning('User canceled import')

            if (
                'mayaReference' in iAObj.options and
                iAObj.options['mayaReference']
            ):
                preserveReferences = iAObj.options['mayaReference']

            self.oldData = set(mc.ls())

            nodes = mc.file(
                iAObj.filePath,
                type=importType,
                i=self.importAssetBool,
                reference=self.referenceAssetBool,
                groupLocator=False,
                groupReference=groupReferenceBool,
                groupName=iAObj.assetName,
                loadReferenceDepth='all',
                sharedNodes='renderLayersByName',
                preserveReferences=preserveReferences,
                returnNewNodes=True,
                options='v=0',
                **kwargs
            )

            if kwargs.get('open', False):
                mc.file(renameToSave=True)

            self.newData = set(mc.ls())

            # Find the actual groupName
            if iAObj.componentName in ['audio']:
                mc.rename(nodes[0], iAObj.assetName)
            else:
                iAObj.assetName = self.getGroupName(nodes, iAObj.assetName)

            try:
                self.linkToFtrackNode(iAObj)
            except Exception as error:
                print error

        # Restore timeline on asset import.
        mayacon.Connector.setTimeLine()
        return 'Imported ' + iAObj.assetType + ' asset'

    def _determineNameSpace(self, iAObj):
        nameSpaceStr = ':'
        if iAObj.options['mayaAddNamespace']:
            if iAObj.options['mayaNamespace'] == 'File name':
                nameSpaceStr = os.path.basename(iAObj.filePath)
                nameSpaceStr = os.path.splitext(nameSpaceStr)[0]
                # Remove the last bit, which usually is the version
                nameSpaceStr = '_'.join(nameSpaceStr.split('_')[:-1])
            if iAObj.options['mayaNamespace'] == 'Component':
                nameSpaceStr = iAObj.componentName
            if iAObj.options['mayaNamespace'] == 'Custom':
                # Use custom namespace if any is specified.
                if iAObj.options['nameSpaceStr']:
                    nameSpaceStr = iAObj.options['nameSpaceStr']

        return nameSpaceStr

    def getGroupName(self, nodes, assetName):
        '''Return the node among the *nodes* containing the given *assetName*.'''
        for node in nodes:
            splitnode = node.split('|')
            for n in splitnode:
                if assetName in n:
                    return n
        return assetName

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''
        panelComInstance = panelcom.PanelComInstance.instance()

        if hasattr(iAObj, 'customComponentName'):
            componentName = iAObj.customComponentName
        else:
            componentName = 'mayaBinary'

        channels = True
        preserveReferences = False
        constructionHistory = False
        constraints = False
        expressions = False
        shader = False

        if iAObj.options.get('mayaHistory'):
            constructionHistory = iAObj.options['mayaHistory']

        if iAObj.options.get('mayaChannels'):
            channels = iAObj.options['mayaChannels']

        if iAObj.options.get('mayaPreserveref'):
            preserveReferences = iAObj.options['mayaPreserveref']

        if iAObj.options.get('mayaShaders'):
            shader = iAObj.options['mayaShaders']

        if iAObj.options.get('mayaConstraints'):
            constraints = iAObj.options['mayaConstraints']

        if iAObj.options.get('mayaExpressions'):
            expressions = iAObj.options['mayaExpressions']

        if iAObj.options.get('exportMode') == 'Selection':
            exportSelectedMode = True
            exportAllMode = False
        else:
            exportSelectedMode = False
            exportAllMode = True

        publishedComponents = []

        temporaryPath = HelpFunctions.temporaryFile(suffix='.mb')
        publishedComponents.append(
            FTComponent(
                componentname=componentName,
                path=temporaryPath
            )
        )

        mc.file(
            temporaryPath,
            op='v=0',
            typ='mayaBinary',
            preserveReferences=preserveReferences,
            constructionHistory=constructionHistory,
            channels=channels,
            constraints=constraints,
            expressions=expressions,
            shader=shader,
            exportSelected=exportSelectedMode,
            exportAll=exportAllMode,
            force=True
        )

        dependenciesVersion = []
        dependencies = mc.ls(type='ftrackAssetNode')
        for dependency in dependencies:
            dependencyAssetId = mc.getAttr('{0}.assetId'.format(dependency))
            if dependencyAssetId:
                dependencyVersion = ftrack.AssetVersion(dependencyAssetId)
                dependenciesVersion.append(dependencyVersion)

        currentVersion = ftrack.AssetVersion(iAObj.assetVersionId)
        currentVersion.addUsesVersions(versions=dependenciesVersion)

        panelComInstance.emitPublishProgressStep()

        return publishedComponents, 'Published ' + iAObj.assetType + ' asset'

    def getSceneSettingsObj(self, iAObj):
        '''Return default settings for the provided *iAObj*.'''
        iAObjCopy = copy.copy(iAObj)
        iAObjCopy.options['mayaHistory'] = True
        iAObjCopy.options['mayaPreserveref'] = True
        iAObjCopy.options['mayaChannels'] = True
        iAObjCopy.options['mayaExpressions'] = True
        iAObjCopy.options['mayaConstraints'] = True
        iAObjCopy.options['mayaShaders'] = True
        iAObjCopy.options['exportMode'] = 'All'
        iAObjCopy.customComponentName = 'mayaBinaryScene'
        return iAObjCopy

    def changeVersion(self, iAObj=None, applicationObject=None):
        '''Change the version of the asset defined in *iAObj*
        and *applicationObject*
        '''
        ftrackNode = mc.listConnections(
            applicationObject + '.ftrack',
            d=False,
            s=True
        )[0]
        nodeAssetPath = iAObj.filePath

        if not iAObj.assetName.endswith('_AST'):
            iAObj.assetName = '_'.join([
                iAObj.assetType.upper(),
                iAObj.assetName,
                'AST']
            )

        # assetLinkNode = mc.listConnections(ftrackNode + '.assetLink')[0]

        referenceNode = False
        for node in mc.listConnections(ftrackNode + '.assetLink'):
            if mc.nodeType(node) == 'reference':
                if 'sharedReferenceNode' in node:
                    continue
                referenceNode = node

        if ':' not in applicationObject:
            iAObj.options['mayaNamespace'] = False
        else:
            iAObj.options['nameSpaceStr'] = iAObj.assetName.upper()
        if referenceNode:
            mc.file(nodeAssetPath, loadReference=referenceNode)
        else:
            nodes = mc.listConnections(ftrackNode + '.assetLink')
            mc.delete(nodes)
            iAObj.options['importMode'] = 'Import'
            iAObj.options['mayaReference'] = False
            self.importAsset(iAObj)

        self.updateftrackNode(iAObj, ftrackNode)

        return True

    def updateftrackNode(self, iAObj, ftrackNode):
        '''Update informations in *ftrackNode* with the provided *iAObj*. '''
        mc.setAttr(
            '{0}.assetVersion'.format(ftrackNode),
            int(iAObj.assetVersion)
        )
        mc.setAttr(
            '{0}.assetId'.format(ftrackNode),
            iAObj.assetVersionId, type='string'
        )
        mc.setAttr(
            '{0}.assetPath'.format(ftrackNode),
            iAObj.filePath, type='string'
        )
        mc.setAttr(
            '{0}.assetTake'.format(ftrackNode),
            iAObj.componentName, type='string'
        )
        mc.setAttr(
            '{0}.assetComponentId'.format(ftrackNode),
            iAObj.componentId, type='string'
        )

    def linkToFtrackNode(self, iAObj):
        '''Create ftrackNode and populate the connectino wiht the imported asset'''
        ftNodeName = '{0}_ftrackdata'.format(iAObj.assetName)
        count = 0
        while 1:
            if mc.objExists(ftNodeName):
                ftNodeName = ftNodeName + str(count)
                count = count + 1
            else:
                break

        ftNode = mc.createNode('ftrackAssetNode', name=ftNodeName)

        diff = self.newData.difference(self.oldData)
        if not diff:
            print 'no diff found in scene'
            return

        for item in diff:
            if mc.lockNode(item, q=True)[0]:
                mc.lockNode(item, l=False)

            if not mc.attributeQuery('ftrack', n=item, exists=True):
                mc.addAttr(item, ln='ftrack', at='message')

            if not mc.listConnections(item + '.ftrack'):
                mc.connectAttr(ftNode + '.assetLink', item + '.ftrack')

        mc.setAttr(
            '{0}.assetVersion'.format(ftNode),
            int(iAObj.assetVersion)
        )

        mc.setAttr(
            '{0}.assetId'.format(ftNode),
            iAObj.assetVersionId, type='string'
        )

        mc.setAttr(
            '{0}.assetPath'.format(ftNode),
            iAObj.filePath, type='string'
        )

        mc.setAttr(
            '{0}.assetTake'.format(ftNode),
            iAObj.componentName, type='string'
        )

        mc.setAttr(
            '{0}.assetType'.format(ftNode),
            iAObj.assetType, type='string'
        )

        mc.setAttr(
            '{0}.assetComponentId'.format(ftNode),
            iAObj.componentId, type='string'
        )

    @staticmethod
    def importOptions():
        '''Return import options for the component'''

        xml = '''
        <tab name="Options">
            <row name="Import mode" accepts="maya">
                <option type="radio" name="importMode">
                    <optionitem name="Import"/>
                    <optionitem name="Open"/>
                    <optionitem name="Reference" value="True"/>
                </option>
            </row>
            <row name="Preserve References" accepts="maya">
                <option type="checkbox" name="mayaReference" value="True"/>
            </row>
            <row name="Add Namespace" accepts="maya">
                <option type="checkbox" name="mayaAddNamespace" value="True"/>
            </row>
            <row name="Namespace from:" accepts="maya">
                <option type="radio" name="mayaNamespace">
                    <optionitem name="File name" value="True"/>
                    <optionitem name="Component"/>
                    <optionitem name="Custom"/>
                </option>
            </row>
            <row name="Custom Namespace" accepts="maya">
                <option type="string" name="nameSpaceStr" value=""/>
            </row>
        </tab>
        '''
        return xml


class AudioAsset(GenericAsset):
    def __init__(self):
        super(AudioAsset, self).__init__()

    def changeVersion(self, iAObj=None, applicationObject=None):
        '''Change the version of the asset defined in *iAObj*
        and *applicationObject*
        '''
        mc.delete(applicationObject)
        iAObj.assetName = applicationObject
        self.importAsset(iAObj)
        return True

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''
        return None, 'Can only import audio not export'

    @staticmethod
    def importOptions():
        '''Return import options for the component'''
        xml = """
        <tab name="Options">
            <row name="Import mode" accepts="maya">
                <option type="radio" name="importMode">
                    <optionitem name="Import" value="True"/>
                </option>
            </row>
        </tab>
        """
        return xml


class GeometryAsset(GenericAsset):
    def __init__(self):
        super(GeometryAsset, self).__init__()

    def _getAlembicRoots(self, iAObj, shape):
        '''Return alembic roots from *iAObj* and *shape*.'''
        parent_node = mc.listRelatives(shape, p=True, f=True)
        while True:
            _temp = mc.listRelatives(parent_node, p=True, f=True)
            if not _temp:
                return parent_node
            else:
                skip_name = '_'.join(
                    [iAObj.assetType.upper(), iAObj.assetName, 'AST']
                )

                if _temp[0] == skip_name:
                    return parent_node

                _node = mc.listConnections(
                    shape, type='ftrackAssetNode'
                )
                if not _node:
                    return parent_node

            parent_node = _temp

    def changeAlembicVersion(self, iAObj=None, applicationObject=None):
        '''Change the version of Alembic defined in *iAObj*
        and *applicationObject*
        '''
        ftNode = mc.listConnections(applicationObject, type='ftrackAssetNode')
        if not ftNode:
            return
        ftNode = ftNode[0]
        shapes = mc.listConnections(ftNode, sh=True, d=True, s=False, type='shape')
        root_nodes = []
        for shape in shapes:
            results = self._getAlembicRoots(iAObj, shape)
            root_nodes += results

        # Remove duplicates.
        root_nodes = ' '.join(list(set(root_nodes)))
        reparent_node = '_'.join(
            [iAObj.assetType.upper(), iAObj.assetName, 'AST']
        )

        mc.AbcImport(
            iAObj.filePath,
            mode='import',
            connect=root_nodes,
            reparent=reparent_node
        )
        return True

    def changeVersion(self, iAObj=None, applicationObject=None):
        '''Change the version of the asset defined in *iAObj*
        and *applicationObject*
        '''
        if iAObj.componentName == 'alembic':
            return self.changeAlembicVersion(iAObj, applicationObject)
        else:
            return GenericAsset.changeVersion(self, iAObj, applicationObject)

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''

        publishedComponents = []

        totalSteps = self.getTotalSteps(
            steps=[
                iAObj.options['mayaBinary'],
                iAObj.options['alembic'],
                iAObj.options['fbx'],
                iAObj.options['mayaPublishScene']
            ]
        )
        panelComInstance = panelcom.PanelComInstance.instance()
        panelComInstance.setTotalExportSteps(totalSteps)

        if iAObj.options['mayaBinary']:
            iAObj.setTotalSteps = False
            mayaComponents, message = GenericAsset.publishAsset(self, iAObj)
            publishedComponents += mayaComponents

        if iAObj.options['mayaPublishScene']:
            iAObjCopy = self.getSceneSettingsObj(iAObj)
            sceneComponents, message = GenericAsset.publishAsset(
                self, iAObjCopy
            )
            publishedComponents += sceneComponents

        if iAObj.options.get('alembic'):
            if iAObj.options.get('alembicExportMode') == 'Selection':
                nodes = mc.ls(sl=True, long=True)
                selectednodes = None
            else:
                selectednodes = mc.ls(sl=True, long=True)
                nodes = mc.ls(type='transform', long=True)
            objCommand = ''
            for n in nodes:
                objCommand = objCommand + '-root ' + n + ' '
            mc.loadPlugin('AbcExport.so', qt=1)

            temporaryPath = HelpFunctions.temporaryFile(suffix='.abc')
            publishedComponents.append(
                FTComponent(
                    componentname='alembic',
                    path=temporaryPath
                )
            )

            alembicJobArgs = ''

            if iAObj.options.get('alembicUvwrite'):
                alembicJobArgs += '-uvWrite '

            if iAObj.options.get('alembicWorldspace'):
                alembicJobArgs += '-worldSpace '

            if iAObj.options.get('alembicWritevisibility'):
                alembicJobArgs += '-writeVisibility '

            if iAObj.options.get('alembicAnimation'):
                alembicJobArgs += '-frameRange {0} {1} -step {2} '.format(
                    iAObj.options['frameStart'],
                    iAObj.options['frameEnd'],
                    iAObj.options['alembicEval']
                )

            alembicJobArgs += ' ' + objCommand + '-file ' + temporaryPath

            mc.AbcExport(j=alembicJobArgs)

            if selectednodes:
                mc.select(selectednodes)

            panelComInstance.emitPublishProgressStep()

        if iAObj.options.get('fbx'):
            temporaryPath = HelpFunctions.temporaryFile(suffix='.fbx')

            # protect windows characters
            temporaryPath = temporaryPath.replace('\\', '\\\\')
            publishedComponents.append(
                FTComponent(
                    componentname='fbx',
                    path=temporaryPath
                )
            )

            # fbx basic options
            mel.eval('FBXResetExport')
            mel.eval('FBXExportConvertUnitString "cm"')
            mel.eval('FBXExportGenerateLog -v 0')

            # fbx user options
            scale = iAObj.options.get('FBXExportScaleFactor')
            mel.eval('FBXExportScaleFactor {}'.format(scale))

            up_axis = iAObj.options.get('FBXExportUpAxis')
            mel.eval('FBXExportUpAxis {}'.format(up_axis))

            version = iAObj.options.get('FBXExportFileVersion')
            mel.eval('FBXExportFileVersion {}'.format(version))

            smooth_mesh = iAObj.options.get('FBXExportSmoothMesh')
            mel.eval('FBXExportSmoothMesh -v {}'.format(int(smooth_mesh)))

            ascii_export = iAObj.options.get('FBXExportInAscii')
            mel.eval('FBXExportInAscii -v {}'.format(int(ascii_export)))

            anim_only = iAObj.options.get('FBXExportAnimationOnly')
            mel.eval('FBXExportAnimationOnly -v {}'.format(int(anim_only)))

            intances = iAObj.options.get('FBXExportInstances')
            mel.eval('FBXExportInstances -v {}'.format(int(intances)))

            constraint_reducer = iAObj.options.get('FBXExportApplyConstantKeyReducer')
            mel.eval('FBXExportApplyConstantKeyReducer -v {}'.format(int(constraint_reducer)))

            bake_complex_anim = iAObj.options.get('FBXExportBakeComplexAnimation')
            mel.eval('FBXExportBakeComplexAnimation -v {}'.format(int(bake_complex_anim)))

            bake_resample_anim = iAObj.options.get('FBXExportBakeResampleAnimation')
            mel.eval('FBXExportBakeResampleAnimation -v {}'.format(int(bake_resample_anim)))

            export_camera = iAObj.options.get('FBXExportCameras')
            mel.eval('FBXExportCameras -v {}'.format(int(export_camera)))

            export_constraints = iAObj.options.get('FBXExportConstraints')
            mel.eval('FBXExportConstraints -v {}'.format(int(export_constraints)))

            embedded_textures = iAObj.options.get('FBXExportEmbeddedTextures')
            mel.eval('FBXExportEmbeddedTextures -v {}'.format(int(embedded_textures)))

            export_lights = iAObj.options.get('FBXExportLights')
            mel.eval('FBXExportLights -v {}'.format(int(export_lights)))

            # fbx export command
            fbx_export_cmd = 'FBXExport -f "{}"'.format(temporaryPath)

            if iAObj.options.get('fbxExportMode') == 'Selection':
                fbx_export_cmd += ' -s'

            mel.eval(fbx_export_cmd)

            if selectednodes:
                mc.select(selectednodes)

            panelComInstance.emitPublishProgressStep()


        return publishedComponents, 'Published GeometryAsset asset'

    @staticmethod
    def exportOptions():
        '''Return the options for exporting the component'''

        xml = """
        <tab name="Maya binary options" accepts="maya">
            <row name="Maya binary" accepts="maya">
                <option type="checkbox" name="mayaBinary" value="True"/>
            </row>
            <row name="Preserve references" accepts="maya">
                <option type="checkbox" name="mayaPreserveref"/>
            </row>
            <row name="History" accepts="maya">
                <option type="checkbox" name="mayaHistory"/>
            </row>
            <row name="Channels" accepts="maya">
                <option type="checkbox" name="mayaChannels" value="True"/>
            </row>
            <row name="Expressions" accepts="maya">
                <option type="checkbox" name="mayaExpressions"/>
            </row>
            <row name="Constraints" accepts="maya">
                <option type="checkbox" name="mayaConstraints"/>
            </row>
            <row name="Shaders" accepts="maya">
                <option type="checkbox" name="mayaShaders" value="True"/>
            </row>
            <row name="Attach scene to asset" accepts="maya">
                <option type="checkbox" name="mayaPublishScene"/>
            </row>
            <row name="Maya Binary Selection Mode" accepts="maya">
                <option type="radio" name="exportMode">
                        <optionitem name="All"/>
                        <optionitem name="Selection" value="True"/>
                </option>
            </row>
        </tab>
        <tab name="Alembic options" enabled="{2}">
            <row name="Publish Alembic">
                <option type="checkbox" name="alembic" value="{2}"/>
            </row>
            <row name="Include animation">
                <option type="checkbox" name="alembicAnimation"/>
            </row>
            <row name="Frame range">
                <option type="string" name="frameStart" value="{0}"/>
                <option type="string" name="frameEnd" value="{1}"/>
            </row>
            <row name="UV Write" accepts="maya">
                <option type="checkbox" name="alembicUvwrite" value="True"/>
            </row>
            <row name="World space" accepts="maya">
                <option type="checkbox" name="alembicWorldspace" value="True"/>
            </row>
            <row name="Write visibility" accepts="maya">
                <option type="checkbox" name="alembicWritevisibility" value="True"/>
            </row>
            <row name="Evaluate every">
                <option type="float" name="alembicEval" value="1.0"/>
            </row>
            <row name="Alembic Selection Mode" accepts="maya">
                <option type="radio" name="alembicExportMode">
                        <optionitem name="All"/>
                        <optionitem name="Selection" value="True"/>
                </option>
            </row>
        </tab>
        <tab name="Fbx options">
            <row name="Publish Fbx">
                <option type="checkbox" name="fbx" value="True"/>
            </row>
            <row name="Ascii format" accepts="maya">
                <option type="checkbox" name="FBXExportInAscii" value="False"/>
            </row>
            <row name="Scale factor" accepts="maya">
                <option type="string" name="FBXExportScaleFactor" value="1"/>
            </row>
            <row name="Up Axis" accepts="maya">
                <option type="string" name="FBXExportUpAxis" value="y"/>
            </row>
            <row name="File version" accepts="maya">
                <option type="string" name="FBXExportFileVersion" value="FBX201600"/>
            </row>
            <row name="Export Cameras" accepts="maya">
                <option type="checkbox" name="FBXExportCameras" value="True"/>
            </row>
            <row name="Export Lights" accepts="maya">
                <option type="checkbox" name="FBXExportLights" value="True"/>
            </row>
            <row name="Export Constraints" accepts="maya">
                <option type="checkbox" name="FBXExportConstraints" value="False"/>
            </row>
            <row name="Export Instances" accepts="maya">
                <option type="checkbox" name="FBXExportInstances" value="True"/>
            </row>
            <row name="Smooth Mesh" accepts="maya">
                <option type="checkbox" name="FBXExportSmoothMesh" value="False"/>
            </row>
            <row name="Embedded Textures" accepts="maya">
                <option type="checkbox" name="FBXExportEmbeddedTextures" value="False"/>
            </row>
            <row name="Export Animation Only" accepts="maya">
                <option type="checkbox" name="FBXExportAnimationOnly" value="False"/>
            </row>
            <row name="Apply Constant Key Reducer" accepts="maya">
                <option type="checkbox" name="FBXExportApplyConstantKeyReducer" value="False"/>
            </row>
            <row name="Bake Complex Animation" accepts="maya">
                <option type="checkbox" name="FBXExportBakeComplexAnimation" value="False"/>
            </row>
            <row name="Bake Resample Animation" accepts="maya">
                <option type="checkbox" name="FBXExportBakeResampleAnimation" value="False"/>
            </row>
            <row name="FBX Selection Mode" accepts="maya">
                <option type="radio" name="fbxExportMode">
                        <optionitem name="All" value="True"/>
                        <optionitem name="Selection"/>
                </option>
            </row>
        </tab>
        """
        try:
            mc.loadPlugin('AbcImport.so', qt=1)
            alembicEnabled = True
        except:
            alembicEnabled = False

        s = os.getenv('FS', currentStartFrame)
        e = os.getenv('FE', currentEndFrame)
        xml = xml.format(s, e, str(alembicEnabled))
        return xml


class CameraAsset(GenericAsset):

    def __init__(self):
        super(CameraAsset, self).__init__()

    def importAsset(self, iAObj=None):
        '''Import asset defined in *iAObj*'''

        result = GenericAsset.importAsset(self, iAObj)
        if iAObj.options['cameraRenderableMaya']:
            if self.referenceAssetBool:
                cameras = mc.listRelatives(
                    iAObj.assetName, allDescendents=True, type='camera'
                )
            else:
                diff = list(self.newData.difference(self.oldData))
                cameras = mc.ls(diff, type='camera')
            for cam in cameras:
                mc.setAttr('{0}.renderable'.format(cam), True)

        return result

    def changeVersion(self, iAObj=None, applicationObject=None):
        '''Change the version of the asset defined in *iAObj*
        and *applicationObject*
        '''
        result = GenericAsset.changeVersion(self, iAObj, applicationObject)
        return result

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''
        pubMessage = 'Published cameraasset asset'

        # Only export selection when exporting camera
        iAObj.options['exportMode'] = 'Selection'
        publishedComponents = []

        totalSteps = self.getTotalSteps(
            steps=[
                iAObj.options['cameraBake'],
                iAObj.options['cameraMaya'],
                iAObj.options['cameraAlembic'],
                iAObj.options['mayaPublishScene']
            ]
        )
        panelComInstance = panelcom.PanelComInstance.instance()
        panelComInstance.setTotalExportSteps(totalSteps + 1)

        # Get original selection
        nodes = mc.ls(sl=True)

        # Get camera shape and parent transforms
        cameraShape = ''
        for node in nodes:
            if mc.nodeType(node) == 'camera':
                cameraShape = node
            else:
                cameraShapes = mc.listRelatives(
                    node, allDescendents=True, type='camera'
                )
                if len(cameraShapes) > 0:
                    # We only care about one camera
                    cameraShape = cameraShapes[0]

        if cameraShape == '':
            return None, 'No camera selected'

        cameraTransform = mc.listRelatives(
            cameraShape, type='transform', parent=True
        )
        cameraTransform = cameraTransform[0]

        if iAObj.options['cameraBake']:
            tmpCamComponents = mc.duplicate(cameraTransform, un=1, rc=1)
            if mc.nodeType(tmpCamComponents[0]) == 'transform':
                tmpCam = tmpCamComponents[0]
            else:
                tmpCam = mc.ls(tmpCamComponents, type='transform')[0]
            pConstraint = mc.parentConstraint(cameraTransform, tmpCam)
            try:
                mc.parent(tmpCam, world=True)
            except RuntimeError:
                print 'camera already in world space'

            mc.bakeResults(
                tmpCam,
                simulation=True,
                t=(
                    float(iAObj.options['frameStart']),
                    float(iAObj.options['frameEnd'])
                ),
                sb=1,
                at=['tx', 'ty', 'tz', 'rx', 'ry', 'rz'],
                hi='below')

            mc.delete(pConstraint)
            cameraTransform = tmpCam
            panelComInstance.emitPublishProgressStep()

        if iAObj.options['cameraLock']:
            # Get original lock values so we can revert after exporting
            origCamLocktx = mc.getAttr(
                '{0}.tx'.format(cameraTransform), l=True
            )
            origCamLockty = mc.getAttr(
                '{0}.ty'.format(cameraTransform), l=True
            )
            origCamLocktz = mc.getAttr(
                '{0}.tz'.format(cameraTransform), l=True
            )
            origCamLockrx = mc.getAttr(
                '{0}.rx'.format(cameraTransform), l=True
            )
            origCamLockry = mc.getAttr(
                '{0}.ry'.format(cameraTransform), l=True
            )
            origCamLockrz = mc.getAttr(
                '{0}.rz'.format(cameraTransform), l=True
            )
            origCamLocksx = mc.getAttr(
                '{0}.sx'.format(cameraTransform), l=True
            )
            origCamLocksy = mc.getAttr(
                '{0}.sy'.format(cameraTransform), l=True
            )
            origCamLocksz = mc.getAttr(
                '{0}.sz'.format(cameraTransform), l=True
            )

            # Lock transform
            mc.setAttr(
                '{0}.tx'.format(cameraTransform), l=True
            )
            mc.setAttr(
                '{0}.ty'.format(cameraTransform), l=True
            )
            mc.setAttr(
                '{0}.tz'.format(cameraTransform), l=True
            )
            mc.setAttr(
                '{0}.rx'.format(cameraTransform), l=True
            )
            mc.setAttr(
                '{0}.ry'.format(cameraTransform), l=True
            )
            mc.setAttr(
                '{0}.rz'.format(cameraTransform), l=True
            )
            mc.setAttr(
                '{0}.sx'.format(cameraTransform), l=True
            )
            mc.setAttr(
                '{0}.sy'.format(cameraTransform), l=True
            )
            mc.setAttr(
                '{0}.sz'.format(cameraTransform), l=True
            )

        if iAObj.options['cameraMaya']:
            iAObj.setTotalSteps = False
            mayaComponents, message = GenericAsset.publishAsset(self, iAObj)
            publishedComponents += mayaComponents

        if iAObj.options['cameraAlembic']:
            mc.loadPlugin('AbcExport.so', qt=1)
            temporaryPath = HelpFunctions.temporaryFile(suffix='.abc')
            publishedComponents.append(
                FTComponent(
                    componentname='alembic',
                    path=temporaryPath
                )
            )

            alembicJobArgs = ''
            alembicJobArgs += '-fr {0} {1}'.format(
                iAObj.options['frameStart'],
                iAObj.options['frameEnd']
            )
            objCommand = '-root ' + cameraTransform + ' '
            alembicJobArgs += ' ' + objCommand + '-file ' + temporaryPath
            alembicJobArgs += ' -step ' + str(iAObj.options['alembicSteps'])
            try:
                mc.AbcExport(j=alembicJobArgs)
            except:
                import traceback
                var = traceback.format_exc()
                return None, var
            panelComInstance.emitPublishProgressStep()

        if iAObj.options['cameraLock']:
            # Revert camera locks to original
            mc.setAttr('{0}.tx'.format(cameraTransform), l=origCamLocktx)
            mc.setAttr('{0}.ty'.format(cameraTransform), l=origCamLockty)
            mc.setAttr('{0}.tz'.format(cameraTransform), l=origCamLocktz)
            mc.setAttr('{0}.rx'.format(cameraTransform), l=origCamLockrx)
            mc.setAttr('{0}.ry'.format(cameraTransform), l=origCamLockry)
            mc.setAttr('{0}.rz'.format(cameraTransform), l=origCamLockrz)
            mc.setAttr('{0}.sx'.format(cameraTransform), l=origCamLocksx)
            mc.setAttr('{0}.sy'.format(cameraTransform), l=origCamLocksy)
            mc.setAttr('{0}.sz'.format(cameraTransform), l=origCamLocksz)

        if iAObj.options['cameraBake']:
            mc.delete(cameraTransform)
        # Set back original selection
        mc.select(nodes)
        panelComInstance.emitPublishProgressStep()

        if iAObj.options['mayaPublishScene']:
            iAObjCopy = self.getSceneSettingsObj(iAObj)
            sceneComponents, message = GenericAsset.publishAsset(
                self, iAObjCopy
            )
            publishedComponents += sceneComponents

        return publishedComponents, pubMessage

    @staticmethod
    def importOptions():
        '''Return import options for the component'''
        xml = '''
        <tab name="Options">
            <row name="Set all cameras renderable" accepts="maya">
                <option type="checkbox" name="cameraRenderableMaya" value="True"/>
            </row>
            <row name="Import mode" accepts="maya">
                <option type="radio" name="importMode">
                    <optionitem name="Reference" value="True"/>
                    <optionitem name="Import"/>
                </option>
            </row>
            <row name="Preserve References" accepts="maya">
                <option type="checkbox" name="mayaReference" value="True"/>
            </row>
            <row name="Add Namespace" accepts="maya">
                <option type="checkbox" name="mayaAddNamespace" value="True"/>
            </row>
            <row name="Namespace from:" accepts="maya">
                <option type="radio" name="mayaNamespace">
                    <optionitem name="File name" value="True"/>
                    <optionitem name="Component"/>
                    <optionitem name="Custom"/>
                </option>
            </row>
            <row name="Custom Namespace" accepts="maya">
                <option type="string" name="nameSpaceStr" value=""/>
            </row>
        </tab>
        '''
        return xml

    @staticmethod
    def exportOptions():
        '''Return the options for exporting the component'''
        xml = '''
        <tab name="Options">
            <row name="Frame range">
                <option type="string" name="frameStart" value="{0}"/>
                <option type="string" name="frameEnd" value="{1}"/>
            </row>
            <row name="Include Mayabinary camera" accepts="maya">
                <option type="checkbox" name="cameraMaya" value="True"/>
            </row>
            <row name="Bake camera" accepts="maya,nuke">
                <option type="checkbox" name="cameraBake"/>
            </row>
            <row name="Lock camera" accepts="maya,nuke">
                <option type="checkbox" name="cameraLock" value="True"/>
            </row>
            <row name="History" accepts="maya">
                <option type="checkbox" name="mayaHistory" value="True"/>
            </row>
            <row name="Expressions" accepts="maya">
                <option type="checkbox" name="mayaExpressions" value="True"/>
            </row>
            <row name="Export" accepts="maya">
                <option type="radio" name="exportMode">
                        <optionitem name="Selection" value="True"/>
                </option>
            </row>
            <row name="Attach scene to asset" accepts="maya">
                <option type="checkbox" name="mayaPublishScene"/>
            </row>
        </tab>

        <tab name="Alembic options" enabled="{2}">
            <row name="Publish Alembic">
                <option type="checkbox" name="cameraAlembic" value="{2}"/>
            </row>
            <row name="Include animation">
                <option type="checkbox" name="alembicAnimation"/>
            </row>
            <row name="Frame range">
                <option type="string" name="frameStart" value="{0}"/>
                <option type="string" name="frameEnd" value="{1}"/>
            </row>
            <row name="Evaluate every">
                <option type="float" name="alembicSteps" value="1.0"/>
            </row>
        </tab>
        '''
        try:
            mc.loadPlugin('AbcImport.so', qt=1)
            alembicEnabled = True
        except:
            alembicEnabled = False

        s = os.getenv('FS', currentStartFrame)
        e = os.getenv('FE', currentEndFrame)
        xml = xml.format(s, e, str(alembicEnabled))
        return xml


class RigAsset(GenericAsset):
    def __init__(self):
        super(RigAsset, self).__init__()

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''

        totalSteps = self.getTotalSteps(
            steps=[True, iAObj.options['mayaPublishScene']]
        )
        panelComInstance = panelcom.PanelComInstance.instance()
        panelComInstance.setTotalExportSteps(totalSteps)

        publishedComponents, message = GenericAsset.publishAsset(self, iAObj)
        if not publishedComponents:
            return publishedComponents, message

        if iAObj.options['mayaPublishScene']:
            iAObjCopy = self.getSceneSettingsObj(iAObj)
            sceneComponents, message = GenericAsset.publishAsset(
                self, iAObjCopy
            )
            publishedComponents += sceneComponents

        return publishedComponents, message

    @staticmethod
    def exportOptions():
        '''Return the options for exporting the component'''

        xml = '''
        <tab name="Options">
            <row name="Preserve references" accepts="maya">
                <option type="checkbox" name="mayaPreserveref" value="True"/>
            </row>
            <row name="History" accepts="maya">
                <option type="checkbox" name="mayaHistory" value="True"/>
            </row>
            <row name="Channels" accepts="maya">
                <option type="checkbox" name="mayaChannels" value="True"/>
            </row>
            <row name="Expressions" accepts="maya">
                <option type="checkbox" name="mayaExpressions" value="True"/>
            </row>
            <row name="Constraints" accepts="maya">
                <option type="checkbox" name="mayaConstraints" value="True"/>
            </row>
            <row name="Shaders" accepts="maya">
                <option type="checkbox" name="mayaShaders" value="True"/>
            </row>
            <row name="Attach scene to asset" accepts="maya">
                <option type="checkbox" name="mayaPublishScene"/>
            </row>
            <row name="Export" accepts="maya">
                <option type="radio" name="exportMode">
                        <optionitem name="All" value="True"/>
                        <optionitem name="Selection"/>
                </option>
            </row>
        </tab>
        '''
        return xml


class SceneAsset(GenericAsset):
    def __init__(self):
        super(SceneAsset, self).__init__()

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''
        panelComInstance = panelcom.PanelComInstance.instance()
        panelComInstance.setTotalExportSteps(1)
        iAObj.customComponentName = 'mayaBinaryScene'
        components, message = GenericAsset.publishAsset(self, iAObj)
        return components, message

    @staticmethod
    def importOptions():
        '''Return import options for the component'''

        xml = '''
        <tab name="Options">
            <row name="Import mode" accepts="maya">
                <option type="radio" name="importMode">
                    <optionitem name="Import"/>
                    <optionitem name="Open"/>
                    <optionitem name="Reference" value="True"/>
                </option>
            </row>
            <row name="Preserve References" accepts="maya">
                <option type="checkbox" name="mayaReference" value="True"/>
            </row>
            <row name="Add Namespace" accepts="maya">
                <option type="checkbox" name="mayaAddNamespace" value="True"/>
            </row>
            <row name="Namespace from:" accepts="maya">
                <option type="radio" name="mayaNamespace">
                    <optionitem name="File name" value="True"/>
                    <optionitem name="Component"/>
                    <optionitem name="Custom"/>
                </option>
            </row>
            <row name="Custom Namespace" accepts="maya">
                <option type="string" name="nameSpaceStr" value=""/>
            </row>
        </tab>
        '''
        return xml

    @staticmethod
    def exportOptions():
        '''Return the options for exporting the component'''

        xml = '''
        <tab name="Options">
            <row name="Preserve references" accepts="maya">
                <option type="checkbox" name="mayaPreserveref" value="True"/>
            </row>
            <row name="History" accepts="maya">
                <option type="checkbox" name="mayaHistory" value="True"/>
            </row>
            <row name="Channels" accepts="maya">
                <option type="checkbox" name="mayaChannels" value="True"/>
            </row>
            <row name="Expressions" accepts="maya">
                <option type="checkbox" name="mayaExpressions" value="True"/>
            </row>
            <row name="Constraints" accepts="maya">
                <option type="checkbox" name="mayaConstraints" value="True"/>
            </row>
            <row name="Shaders" accepts="maya">
                <option type="checkbox" name="mayaShaders" value="True"/>
            </row>
            <row name="Export" accepts="maya">
                <option type="radio" name="exportMode">
                        <optionitem name="All" value="True"/>
                </option>
            </row>
        </tab>
        '''
        return xml


class LightRigAsset(GenericAsset):
    def __init__(self):
        super(LightRigAsset, self).__init__()

    def publishAsset(self, iAObj=None):
        '''Publish the asset defined by the provided *iAObj*.'''

        totalSteps = self.getTotalSteps(
            steps=[True, iAObj.options['mayaPublishScene']]
        )
        panelComInstance = panelcom.PanelComInstance.instance()
        panelComInstance.setTotalExportSteps(totalSteps)

        publishedComponents, message = GenericAsset.publishAsset(self, iAObj)
        if not publishedComponents:
            return publishedComponents, message

        if iAObj.options['mayaPublishScene']:
            iAObjCopy = self.getSceneSettingsObj(iAObj)
            sceneComponents, message = GenericAsset.publishAsset(
                self, iAObjCopy
            )
            publishedComponents += sceneComponents

        return publishedComponents, message

    @staticmethod
    def exportOptions():
        '''Return the options for exporting the component'''

        xml = '''
        <tab name="Options">
            <row name="Preserve references" accepts="maya">
                <option type="checkbox" name="mayaPreserveref"/>
            </row>
            <row name="History" accepts="maya">
                <option type="checkbox" name="mayaHistory"/>
            </row>
            <row name="Channels" accepts="maya">
                <option type="checkbox" name="mayaChannels" value="True"/>
            </row>
            <row name="Expressions" accepts="maya">
                <option type="checkbox" name="mayaExpressions"/>
            </row>
            <row name="Constraints" accepts="maya">
                <option type="checkbox" name="mayaConstraints"/>
            </row>
            <row name="Shaders" accepts="maya">
                <option type="checkbox" name="mayaShaders"/>
            </row>
            <row name="Attach scene to asset" accepts="maya">
                <option type="checkbox" name="mayaPublishScene"/>
            </row>
            <row name="Export" accepts="maya">
                <option type="radio" name="exportMode">
                        <optionitem name="All"/>
                        <optionitem name="Selection" value="True"/>
                </option>
            </row>
        </tab>
        '''
        return xml


class ImageAsset(GenericAsset):
    def __init__(self):
        super(ImageAsset, self).__init__()

    def _createNodes(self, iAObj=None, namespace=None):
        # create file node
        if namespace:
            saved_namespace = mc.namespaceInfo(currentNamespace=True)

            if not mc.namespace(exists=namespace):
                mc.namespace(add=namespace)

            mc.namespace(set=namespace)

        if mc.about(version=True) == '2016':
            # enable color management for textures in Maya 2016
            color_managed = True
        else:
            color_managed = False

        texture_node = mc.shadingNode("file", asTexture=True, name=iAObj.assetName, isColorManaged=color_managed)

        # create place2dTexture node
        place_2d_node = mc.shadingNode("place2dTexture", asUtility=True)

        # connect nodes
        mc.setAttr('%s.fileTextureName' % texture_node, iAObj.filePath, type='string')

        mc.connectAttr('%s.coverage' % place_2d_node, '%s.coverage' % texture_node)
        mc.connectAttr('%s.translateFrame' % place_2d_node, '%s.translateFrame' % texture_node)
        mc.connectAttr('%s.rotateFrame' % place_2d_node, '%s.rotateFrame' % texture_node)
        mc.connectAttr('%s.mirrorU' % place_2d_node, '%s.mirrorU' % texture_node)
        mc.connectAttr('%s.mirrorV' % place_2d_node, '%s.mirrorV' % texture_node)
        mc.connectAttr('%s.stagger' % place_2d_node, '%s.stagger' % texture_node)
        mc.connectAttr('%s.wrapU' % place_2d_node, '%s.wrapU' % texture_node)
        mc.connectAttr('%s.wrapV' % place_2d_node, '%s.wrapV' % texture_node)
        mc.connectAttr('%s.repeatUV' % place_2d_node, '%s.repeatUV' % texture_node)
        mc.connectAttr('%s.offset' % place_2d_node, '%s.offset' % texture_node)
        mc.connectAttr('%s.rotateUV' % place_2d_node, '%s.rotateUV' % texture_node)
        mc.connectAttr('%s.noiseUV' % place_2d_node, '%s.noiseUV' % texture_node)
        mc.connectAttr('%s.vertexUvOne' % place_2d_node, '%s.vertexUvOne' % texture_node)
        mc.connectAttr('%s.vertexUvTwo' % place_2d_node, '%s.vertexUvTwo' % texture_node)
        mc.connectAttr('%s.vertexUvThree' % place_2d_node, '%s.vertexUvThree' % texture_node)
        mc.connectAttr('%s.vertexCameraOne' % place_2d_node, '%s.vertexCameraOne' % texture_node)
        mc.connectAttr('%s.outUV' % place_2d_node, '%s.uv' % texture_node)
        mc.connectAttr('%s.outUvFilterSize' % place_2d_node, '%s.uvFilterSize' % texture_node)

        if namespace:
            mc.namespace(set=saved_namespace)

    def importAsset(self, iAObj=None):
        self.oldData = set(mc.ls())

        if iAObj.options.get('mayaNamespace'):
            file_asset_namespace = os.path.basename(iAObj.filePath)
            file_asset_namespace = os.path.splitext(file_asset_namespace)[0]
            # Remove the last bit, which usually is the version
            file_asset_namespace = '_'.join(file_asset_namespace.split('_')[:-1])
            namespace = iAObj.options.get('nameSpaceStr', None) or file_asset_namespace
        else:
            namespace = None

        self._createNodes(iAObj, namespace)
        self.newData = set(mc.ls())
        self.linkToFtrackNode(iAObj)

    def publishAsset(self, iAObj=None):
        raise ValueError('Cannot publish texture from maya')

    def changeVersion(self, iAObj=None, applicationObject=None):
        node = applicationObject

        # If the node is a place2dTexture node, find the associated file node.
        if mc.nodeType(node) == "place2dTexture":
            connections = mc.listConnections(node + ".rotateUV", d=True, s=False)
            if connections:
                node = connections[0]
            else:
                node = None

        if node:
            mc.setAttr('%s.fileTextureName' % node, iAObj.filePath, type='string')
        else:
            # report some error here?
            return False

        ftrackNode = mc.listConnections(
            applicationObject + '.ftrack',
            d=False,
            s=True
        )[0]

        self.updateftrackNode(iAObj, ftrackNode)
        return True

    def linkToFtrackNode(self, iAObj):
        # Contains small fix for addAttr without short name which usually clash
        diff = self.newData.difference(self.oldData)
        if not diff:
            print 'no diff found in scene'
            return

        ftNodeName = iAObj.assetName + "_ftrackdata"
        count = 0
        while 1:
            if mc.objExists(ftNodeName):
                ftNodeName = ftNodeName + str(count)
                count = count + 1
            else:
                break

        ftNode = mc.createNode("ftrackAssetNode", name=ftNodeName)
        mc.setAttr(ftNode + ".assetVersion", int(iAObj.assetVersion))
        mc.setAttr(ftNode + ".assetId", iAObj.assetVersionId, type="string")
        mc.setAttr(ftNode + ".assetPath", iAObj.filePath, type="string")
        mc.setAttr(ftNode + ".assetTake", iAObj.componentName, type="string")
        mc.setAttr(ftNode + ".assetType", iAObj.assetType, type="string")
        mc.setAttr(
            ftNode + ".assetComponentId",
            iAObj.componentId,
            type="string"
        )

        for item in diff:
            if mc.lockNode(item, q=True)[0]:
                mc.lockNode(item, l=False)

            if not mc.attributeQuery('ftrack', n=item, exists=True):
                mc.addAttr(item, ln="ftrack", at="message")

            if not mc.listConnections(item + ".ftrack"):
                mc.connectAttr(ftNode + ".assetLink", item + ".ftrack")

    @staticmethod
    def importOptions():
        xml = """
        <tab name="Options">
            <row name="Add Asset Namespace" accepts="maya">
                <option type="checkbox" name="mayaNamespace" value="False"/>
                <option type="string" name="nameSpaceStr" value=""/>
            </row>
        </tab>
        """
        return xml


def registerAssetTypes():
    assetHandler = FTAssetHandlerInstance.instance()
    assetHandler.registerAssetType(name='cam', cls=CameraAsset)
    assetHandler.registerAssetType(name='lgt', cls=LightRigAsset)
    assetHandler.registerAssetType(name='rig', cls=RigAsset)
    assetHandler.registerAssetType(name='audio', cls=AudioAsset)
    assetHandler.registerAssetType(name='geo', cls=GeometryAsset)
    assetHandler.registerAssetType(name='scene', cls=SceneAsset)
    assetHandler.registerAssetType(name='img', cls=ImageAsset)
