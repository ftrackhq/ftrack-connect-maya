# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import maya.cmds as mc
import maya.mel as mm
import logging
import ftrack
import functools

from ftrack_connect_maya.connector import Connector
from ftrack_connect_maya.connector.mayacon import DockedWidget
from ftrack_connect.ui.widget.asset_manager import FtrackAssetManagerDialog
from ftrack_connect.ui.widget.import_asset import FtrackImportAssetDialog
from ftrack_connect_maya.ui.info import FtrackMayaInfoDialog
from ftrack_connect_maya.ui.publisher import PublishAssetDialog
from ftrack_connect_maya.ui.tasks import FtrackTasksDialog

ftrack.setup()

currentEntity = ftrack.Task(
    os.getenv('FTRACK_TASKID', os.getenv('FTRACK_SHOTID'))
)


dialogs = [
    (FtrackImportAssetDialog, 'Import asset'),
    (
        functools.partial(PublishAssetDialog, currentEntity=currentEntity),
        'Publish asset'
    ),
    'divider',
    (FtrackAssetManagerDialog, 'Asset manager'),
    'divider',
    (FtrackMayaInfoDialog, 'Info'),
    (FtrackTasksDialog, 'Tasks')
]

created_dialogs = dict()

connector = Connector()


def open_dialog(dialog_class):
    '''Open *dialog_class* and create if not already existing.'''
    dialog_name = dialog_class

    if dialog_name not in created_dialogs:
        ftrack_dialog = dialog_class(connector=connector)
        ftrack_docked_dialog = DockedWidget(ftrack_dialog)
        created_dialogs[dialog_name] = ftrack_docked_dialog

    created_dialogs[dialog_name].show()


def loadAndInit():
    '''Load and Init the maya plugin, build the widgets and set the menu'''
    # Load the ftrack maya plugin
    mc.loadPlugin('ftrackMayaPlugin.py', quiet=True)
    # Create new maya connector and register the assets
    connector.registerAssets()

    # Check if maya is in batch mode
    if mc.about(batch=True):
        return

    gMainWindow = mm.eval('$temp1=$gMainWindow')
    if mc.menu('ftrack', exists=True):
        mc.deleteUI('ftrack')

    ftrackMenu = mc.menu(
        'ftrack',
        parent=gMainWindow,
        tearOff=False,
        label='ftrack'
    )

    # Register and hook the dialog in ftrack menu
    for item in dialogs:
        if item == 'divider':
            mc.menuItem(divider=True)
            continue

        dialog_class, label = item

        mc.menuItem(
            parent=ftrackMenu,
            label=label,
            command=(
                lambda x, dialog_class=dialog_class: open_dialog(dialog_class)
            )
        )


def checkForNewAssets():
    '''Check whether there is any new asset'''
    allObjects = mc.ls(type='ftrackAssetNode')
    message = ''
    for ftNode in allObjects:
        if not mc.referenceQuery(ftNode, isNodeReferenced=True):
            assetVersion = mc.getAttr("{0}.assetVersion".format(ftNode))
            assetId = mc.getAttr("{0}.assetId".format(ftNode))
            if assetId is None:
                mc.warning(
                    'FTrack node "{0}" does not contain data!'.format(ftNode)
                )
                continue

            assetTake = mc.getAttr(ftNode + ".assetTake")
            assetversion = ftrack.AssetVersion(assetId)
            asset = assetversion.getAsset()
            versions = asset.getVersions(componentNames=[assetTake])
            latestVersion = versions[-1].getVersion()
            if latestVersion != assetVersion:
                message = '- {0} can be updated from v:{1} to v:{2}'.format(
                    ftNode, assetVersion, latestVersion
                )

    if message != '':
        confirm = mc.confirmDialog(
            title='New assets',
            message=message,
            button=['Open AssetManager', 'Close'],
            defaultButton='Close',
            cancelButton='Close',
            dismissString='Close'
        )

        if confirm != 'Close':
            global assetManagerDialog
            assetManagerDialog = FtrackAssetManagerDialog(connector=connector)
            assetManagerDialog.show()


def refAssetManager():
    '''Refresh asset manager'''
    from ftrack_connect.connector import panelcom
    panelComInstance = panelcom.PanelComInstance.instance()
    panelComInstance.refreshListeners()


def framerateInit():
    '''Set the initial framerate with the values set on the shot'''
    import ftrack
    shotId = os.getenv('FTRACK_SHOTID')
    shot = ftrack.Shot(id=shotId)
    fps = str(int(shot.get('fps')))

    mapping = {
        '15': 'game',
        '24': 'film',
        '25': 'pal',
        '30': 'ntsc',
        '48': 'show',
        '50': 'palf',
        '60': 'ntscf',
    }

    fpsType = mapping.get(fps, 'pal')
    mc.warning('Setting current unit to {0}'.format(fps))
    mc.currentUnit(time=fpsType)


if not Connector.batch():
    mc.scriptJob(e=["SceneOpened", "checkForNewAssets()"], permanent=True)
    mc.scriptJob(e=["SceneOpened", "refAssetManager()"], permanent=True)
    mc.evalDeferred("loadAndInit()")
    mc.evalDeferred("framerateInit()")
    mc.evalDeferred("Connector.setTimeLine()")


logging.getLogger().setLevel(logging.INFO)
