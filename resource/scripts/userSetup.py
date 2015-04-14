import os
import maya.cmds as mc
import maya.mel as mm
import logging
import ftrack

from ftrack_connect_maya.connector import Connector
from ftrack_connect_maya.connector.mayacon import DockedWidget
from ftrack_connect.ui.widget.import_asset import FtrackImportAssetDialog
from ftrack_connect.ui.widget.asset_manager import FtrackAssetManagerDialog
from ftrack_connect_maya.ui.info import FtrackMayaInfoDialog
from ftrack_connect_maya.ui.publisher import FtrackPublishAssetDialog
from ftrack_connect_maya.ui.tasks import FtrackTasksDialog

ftrack.setup()

dialogs = [
    FtrackImportAssetDialog,
    FtrackAssetManagerDialog,
    FtrackPublishAssetDialog,
    FtrackMayaInfoDialog,
    FtrackTasksDialog
]

connector = Connector()


def loadAndInit():
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

    ftrack_menu = mc.menu(
        'ftrack',
        parent=gMainWindow,
        tearOff=False,
        label='ftrack'
    )

    # Register and hook the dialog in ftrack menu
    for Dialog in dialogs:
        ftrack_dialog = Dialog(connector=connector)
        ftrack_docked_dialog = DockedWidget(ftrack_dialog)

        mc.menuItem(
            parent=ftrack_menu,
            label=ftrack_dialog.windowTitle().replace('ftrack', ''),
            command=lambda x, dialog=ftrack_docked_dialog: dialog.show(),
        )
    mc.menuItem(divider=True)


def checkForNewAssets():
    allObjects = mc.ls(type='ftrackAssetNode')
    message = ''
    for ftNode in allObjects:
        if not mc.referenceQuery(ftNode, isNodeReferenced=True):
            assetVersion = mc.getAttr(ftNode + ".assetVersion")
            assetId = mc.getAttr(ftNode + ".assetId")
            if assetId is None:
                mc.warning('FTrack node "%s" does not contain data!' % ftNode)
            assetTake = mc.getAttr(ftNode + ".assetTake")
            assetversion = ftrack.AssetVersion(assetId)
            asset = assetversion.getAsset()
            versions = asset.getVersions(componentNames=[assetTake])
            latestVersion = versions[-1].getVersion()
            if latestVersion != assetVersion:
                message = '- %s can be updated from v:%d to v:%s' % (
                    ftNode, assetVersion, latestVersion
                )

    if message != '':
        confirm = mc.confirmDialog(title='New assets',
                                   message=message,
                                   button=['Open AssetManager', 'Close'],
                                   defaultButton='Close',
                                   cancelButton='Close',
                                   dismissString='Close')
        if confirm != 'Close':
            global assetManagerDialog
            assetManagerDialog = FtrackAssetManagerDialog(connector=connector)
            assetManagerDialog.show()


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
    mc.warning('Setting current unit to  %s ' % fps)
    mc.currentUnit(time=fps_type)


def timeline_init():
    import ftrack
    start_frame = float(os.getenv('FS', 1001))
    end_frame = float(os.getenv('FE', 1101))
    shot_id = os.getenv('FTRACK_SHOTID')
    shot = ftrack.Shot(id=shot_id)
    handles = float(shot.get('handles'))

    mc.warning('Setting timeline to %s %s ' % (start_frame, end_frame))

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


logging.getLogger().setLevel(logging.INFO)
