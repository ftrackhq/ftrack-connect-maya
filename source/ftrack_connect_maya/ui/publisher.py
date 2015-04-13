from PySide import QtCore, QtGui
from ftrack_connect import connector as ftrack_connector

import getpass
from ftrack_connect_maya.ui.export_asset_options_widget import ExportAssetOptionsWidget
from ftrack_connect_maya.ui.export_options_widget import ExportOptionsWidget

from ftrack_connect.ui.widget import entity_path
from ftrack_connect.ui.widget import entity_browser
from ftrack_connect.ui.widget import header
import ftrack
import os


class ContextSelector(QtGui.QWidget):
    entityChanged = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(ContextSelector, self).__init__(parent=parent)
        self._entity = None

        self.entityBrowser = entity_browser.EntityBrowser()
        self.entityBrowser.setMinimumWidth(600)
        self.entity_path = entity_path.EntityPath()
        self.entityBrowseButton = QtGui.QPushButton('Browse')

        layout = QtGui.QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.entity_path)
        layout.addWidget(self.entityBrowseButton)

        self.entityBrowseButton.clicked.connect(
            self._onEntityBrowseButtonClicked
        )
        self.entityChanged.connect(self.entity_path.setEntity)
        self.entityBrowser.selectionChanged.connect(
            self._onEntityBrowserSelectionChanged
        )

    def reset(self):
        current_entity = os.getenv('FTRACK_TASKID', os.getenv('FTRACK_SHOTID'))
        entity = ftrack.Task(current_entity)
        self.entity_path.setEntity(entity)
        self.entityChanged.emit(entity)

    def setEntity(self, entity):
        '''Set the *entity* for the view.'''
        self._entity = entity
        self.entityChanged.emit(entity)

    def _onEntityBrowseButtonClicked(self):
        '''Handle entity browse button clicked.'''
        # Ensure browser points to parent of currently selected entity.
        if self._entity is not None:
            location = []
            try:
                parents = self._entity.getParents()
            except AttributeError:
                pass
            else:
                for parent in parents:
                    location.append(parent.getId())

            location.reverse()
            self.entityBrowser.setLocation(location)

        # Launch browser.
        if self.entityBrowser.exec_():
            selected = self.entityBrowser.selected()
            if selected:
                self.setEntity(selected[0])
            else:
                self.setEntity(None)

    def _onEntityBrowserSelectionChanged(self, selection):
        '''Handle selection of entity in browser.'''
        self.entityBrowser.acceptButton.setDisabled(True)
        if len(selection) == 1:
            entity = selection[0]

            # Prevent selecting Projects or Tasks directly under a Project to
            # match web interface behaviour.
            if isinstance(entity, ftrack.Task):
                objectType = entity.getObjectType()
                if (
                    objectType == 'Task'
                    and isinstance(entity.getParent(), ftrack.Project)
                ):
                    return

                self.entityBrowser.acceptButton.setDisabled(False)


class FtrackPublishAssetDialog(QtGui.QDialog):
    def __init__(self, parent=None, connector=None):
        if not connector:
            raise ValueError(
                'Please provide a connector object for {0}'.format(
                    self.__class__.__name__
                )
            )
        self.connector = connector
        if not parent:
            self.parent = self.connector.getMainWindow()

        super(FtrackPublishAssetDialog, self).__init__(self.parent)
        self.setSizePolicy(
            QtGui.QSizePolicy(
                QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding
            )
        )

        self.assetType = None
        self.assetName = None
        self.status = None

        self.mainLayout = QtGui.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.mainWidget = QtGui.QWidget(self)
        self.scrollLayout = QtGui.QVBoxLayout(self.mainWidget)
        self.scrollLayout.setSpacing(6)

        self.scrollArea = QtGui.QScrollArea(self)
        self.mainLayout.addWidget(self.scrollArea)

        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollArea.setLineWidth(0)
        self.scrollArea.setFrameShape(QtGui.QFrame.NoFrame)
        self.scrollArea.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )
        self.scrollArea.setWidget(self.mainWidget)

        self.headerWidget = header.Header(getpass.getuser(), self)
        self.scrollLayout.addWidget(self.headerWidget)

        if 'FTRACK_TASKID' in os.environ:
            self.browseMode = 'Task'
        else:
            self.browseMode = 'Shot'

        self.browseTasksWidget = ContextSelector(
            self
        )

        self.scrollLayout.addWidget(self.browseTasksWidget)

        self.exportAssetOptionsWidget = ExportAssetOptionsWidget(
            self, browseMode=self.browseMode
        )

        self.scrollLayout.addWidget(self.exportAssetOptionsWidget)

        self.exportOptionsWidget = ExportOptionsWidget(
            self, connector=self.connector
        )

        self.scrollLayout.addWidget(self.exportOptionsWidget)

        spacerItem = QtGui.QSpacerItem(
            20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding
        )
        self.scrollLayout.addItem(spacerItem)

        self.setObjectName('ftrackPublishAsset')
        self.setWindowTitle("ftrackPublishAsset")
        panelComInstance = ftrack_connector.panelcom.PanelComInstance.instance()
        panelComInstance.addSwitchedShotListener(self.browseTasksWidget.reset)
        panelComInstance.addSwitchedShotListener(self.resetOptions)

        self.exportAssetOptionsWidget.clickedAssetTypeSignal.connect(
            self.exportOptionsWidget.setStackedWidget
        )

        self.browseTasksWidget.entityChanged.connect(
            self.exportAssetOptionsWidget.updateView
        )

        self.exportOptionsWidget.ui.publishButton.clicked.connect(
            self.publishAsset
        )

        panelComInstance.publishProgressSignal.connect(
            self.exportOptionsWidget.setProgress
        )

        self.browseTasksWidget.reset()

    def resetOptions(self):
        self.exportOptionsWidget.resetOptions()
        self.exportAssetOptionsWidget.setAssetType(self.assetType)
        self.exportAssetOptionsWidget.setAssetName(self.assetName)
        self.exportOptionsWidget.setComment('')
        self.exportOptionsWidget.ui.thumbnailLineEdit.setText('')

        task = ftrack.Task(
            os.getenv('FTRACK_TASKID',
                os.getenv('FTRACK_SHOTID')
            )
        )

        self.exportAssetOptionsWidget.updateTasks(ftrack_entity=task)
        self.exportAssetOptionsWidget.updateView(ftrack_entity=task)

    def setAssetType(self, assetType):
        self.exportAssetOptionsWidget.setAssetType(assetType)
        self.assetType = assetType

    def setAssetName(self, assetName):
        self.exportAssetOptionsWidget.setAssetName(assetName)
        self.assetName = assetName

    def setComment(self, comment):
        self.exportOptionsWidget.setComment(comment)

    def publishAsset(self):
        task = self.exportAssetOptionsWidget.getTask()
        taskId = task.getId()
        shot = self.exportAssetOptionsWidget.getShot()

        assettype = self.exportAssetOptionsWidget.getAssetType()
        assetName = self.exportAssetOptionsWidget.getAssetName()
        status = self.exportAssetOptionsWidget.getStatus()

        comment = self.exportOptionsWidget.getComment()
        options = self.exportOptionsWidget.getOptions()
        thumbnail = self.exportOptionsWidget.getThumbnail()

        if assetName == '':
            self.showWarning('Missing assetName', 'assetName can not be blank')
            return

        prePubObj = ftrack_connector.FTAssetObject(
            options=options, taskId=taskId
        )

        result, message = self.connector.prePublish(prePubObj)

        if not result:
            self.showWarning('Prepublish failed', message)
            return

        self.exportOptionsWidget.setProgress(0)
        asset = shot.createAsset(assetName, assettype)

        assetVersion = asset.createVersion(comment=comment, taskid=taskId)

        pubObj = ftrack_connector.FTAssetObject(
            assetVersionId=assetVersion.getId(),
            options=options
        )

        publishedComponents, message = self.connector.publishAsset(pubObj)
        if publishedComponents:
            self.connector.publishAssetFiles(
                publishedComponents, assetVersion, pubObj
            )
        else:
            self.exportOptionsWidget.setProgress(100)

        # Update status of task.
        ft_task = ftrack.Task(id=taskId)
        if (
            ft_task and
            ft_task.get('object_typeid') == '11c137c0-ee7e-4f9c-91c5-8c77cec22b2c'
        ):
            for taskStatus in ftrack.getTaskStatuses():
                if (
                    taskStatus.getName() == status and
                    taskStatus.get('statusid') != ft_task.get('statusid')
                ):
                    try:
                        ft_task.setStatus(taskStatus)
                    except Exception, error:
                        print 'warning: %s ' % error

                    break

        if thumbnail != '':
            assetVersion.createThumbnail(thumbnail)

        self.headerWidget.setMessage(message, 'info')
        self.exportOptionsWidget.setComment('')
        self.resetOptions()
        self.exportAssetOptionsWidget.emitAssetType(
            self.exportAssetOptionsWidget.ui.ListAssetsComboBox.currentIndex()
        )

    def getShotPath(self, shot):
        shotparents = shot.getParents()
        shotpath = ''

        for parent in reversed(shotparents):
            shotpath += parent.getName() + '.'
        shotpath += shot.getName()
        return shotpath

    def showWarning(self, subject, message):
        self.headerWidget.setMessage(message, 'warning')
