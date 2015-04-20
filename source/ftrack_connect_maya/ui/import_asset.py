# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import ftrack
from ftrack_connect.connector import PanelComInstance
from ftrack_connect.ui.widget.import_asset import (
    FtrackImportAssetDialog as _FtrackImportAssetDialog
)
from context_selector import ContextSelector


class FtrackImportAssetDialog(_FtrackImportAssetDialog):
    def __init__(self, parent=None, connector=None):
        super(FtrackImportAssetDialog, self).__init__(
            parent=parent, connector=connector
        )

        self.currentEntity = ftrack.Task(
            os.getenv('FTRACK_TASKID',
                os.getenv('FTRACK_SHOTID')
            )
        )

        self.browseTasksWidget.setParent(None)
        self.browseTasksWidget = ContextSelector(
            currentEntity=self.currentEntity, parent=self
        )
        self.verticalLayout.insertWidget(1, self.browseTasksWidget)

        panelComInstance = PanelComInstance.instance()
        panelComInstance.addSwitchedShotListener(
            self.browseTasksWidget.reset
        )
        self.browseTasksWidget.entityChanged.connect(self.clickedIdSignal)
        self.browseTasksWidget.reset()

    def clickedIdSignal(self, ftrack_entity):
        '''Handle click signal.'''
        ftrackId = None

        if isinstance(ftrack_entity, ftrack.Task):
            ftrackId = ftrack_entity.getId()

        elif isinstance(ftrack_entity, basestring):
            ftrackId = str(ftrack_entity)

        self.listAssetsTableWidget.initView(ftrackId)
