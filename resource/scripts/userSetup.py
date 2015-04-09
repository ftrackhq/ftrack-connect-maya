import os
import maya.cmds as mc
import maya.mel as mm

from ftrack_connect_maya.connector import Connector
from ftrack_connect_maya.connector.mayacon import DockedWidget
from ftrack_connect.ui.widget.import_asset import FtrackImportAssetDialog
from ftrack_connect.ui.widget.asset_manager import FtrackAssetManagerDialog
from ftrack_connect_maya.ui.publisher import FtrackPublishAssetDialog

dialogs = [
    FtrackImportAssetDialog,
    FtrackAssetManagerDialog,
    FtrackPublishAssetDialog
]


def loadAndInit():
    mc.loadPlugin('ftrackMayaPlugin.py', quiet=True)

    connector = Connector()
    connector.registerAssets()

    if mc.about(batch=True):
        return

    gMainWindow = mm.eval('$temp1=$gMainWindow')
    if mc.menu('ftrack', exists=True):
        mc.deleteUI('ftrack')

    ftrack_menu = mc.menu(
        'ftrack',
        parent=gMainWindow,
        tearOff=False,
        label='ftrack'
    )

    for Dialog in dialogs:
        ftrack_dialog = Dialog(connector=connector)
        ftrack_docked_dialog = DockedWidget(ftrack_dialog)

        mc.menuItem(
            parent=ftrack_menu,
            label=ftrack_dialog.windowTitle(),
            command=lambda x, dialog=ftrack_docked_dialog: dialog.show(),
        )

    import ftrack
    ftrack.setup()


def checkForNewAssets():
    allObjects = mc.ls(type='ftrackAssetNode')
    message = ''
    import ftrack
    for ftNode in allObjects:
        if not mc.referenceQuery(ftNode, isNodeReferenced=True):
            assetVersion = mc.getAttr(ftNode + ".assetVersion")
            assetId = mc.getAttr(ftNode + ".assetId")
            if assetId is None:
                print 'WARNING: FTrack node "%s" does not contain data!' % ftNode
            assetTake = mc.getAttr(ftNode + ".assetTake")
            assetversion = ftrack.AssetVersion(assetId)
            asset = assetversion.getAsset()
            versions = asset.getVersions(componentNames=[assetTake])
            latestversion = versions[-1].getVersion()
            if latestversion != assetVersion:
                message += ftNode + ' can be updated from v:' + str(assetVersion)
                message += ' to v:' + str(latestversion) + '\n'

    if message != '':
        confirm = mc.confirmDialog(title='New assets',
                                   message=message,
                                   button=['Open AssetManager', 'Close'],
                                   defaultButton='Close',
                                   cancelButton='Close',
                                   dismissString='Close')
        if confirm != 'Close':
            from ftrackplugin import ftrackDialogs
            global ftrackAssetManagerDialogWindow
            ftrackAssetManagerDialogWindow = ftrackDialogs.ftrackAssetManagerDialog()
            ftrackAssetManagerDialogWindow.show()


def refAssetManager():
    from ftrack_connect.connector import panelcom
    panelComInstance = panelcom.PanelComInstance.instance()
    panelComInstance.refreshListeners()



def framerate_init():
    import ftrack
    shot_id = os.getenv('FTRACK_SHOTID')
    shot = ftrack.Shot(id=shot_id)
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

    fps_type = mapping.get(fps, 'pal')
    mc.currentUnit(time=fps_type)


def timeline_init():
    import ftrack
    start_frame = float(os.getenv('FS', 1001))
    end_frame = float(os.getenv('FE', 1101))
    shot_id = os.getenv('FTRACK_SHOTID')
    shot = ftrack.Shot(id=shot_id)
    handles = float(shot.get('handles'))

    print 'setting timeline to %s %s ' % (start_frame, end_frame)

    # add handles to start and end frame
    hsf = start_frame - handles
    hef = end_frame + handles

    mc.playbackOptions(
        minTime=hsf,
        maxTime=hef,

        animationStartTime=hsf,
        animationEndTime=hef
    )


if not Connector.batch():
    mc.scriptJob(e=["SceneOpened", "checkForNewAssets()"], permanent=True)
    mc.scriptJob(e=["SceneOpened", "refAssetManager()"], permanent=True)
    mc.evalDeferred("loadAndInit()")
    mc.evalDeferred("framerate_init()")
    mc.evalDeferred("timeline_init()")

import logging

logging.getLogger().setLevel(logging.INFO)
