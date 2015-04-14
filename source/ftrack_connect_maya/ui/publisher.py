from PySide import QtCore, QtGui
from ftrack_connect import connector as ftrack_connector

import getpass
from ftrack_connect.ui.widget.browse_tasks_small import BrowseTasksSmallWidget
from ftrack_connect_maya.ui.export_asset_options_widget import ExportAssetOptionsWidget
from ftrack_connect_maya.ui.export_options_widget import ExportOptionsWidget
from ftrack_connect.ui.widget import header
import ftrack
import os


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
        # self.headerWidget.setTitle('Publish Asset')
        self.scrollLayout.addWidget(self.headerWidget)

        # BrowseTasksSmallWidget uses a floating position so it needs
        # to know where its top is
        if 'FTRACK_TASKID' in os.environ:
            self.browseMode = 'Task'
        else:
            self.browseMode = 'Shot'

        self.browseTasksWidget = BrowseTasksSmallWidget(
            self, browseMode=self.browseMode
        )

        self.scrollLayout.addWidget(self.browseTasksWidget)
        pos = self.headerWidget.rect().bottomRight().y()
        self.browseTasksWidget.setTopPosition(pos)
        self.browseTasksWidget.setLabelText('Publish to')

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
        panelComInstance.addSwitchedShotListener(self.browseTasksWidget.updateTask)
        panelComInstance.addSwitchedShotListener(self.resetOptions)

        QtCore.QObject.connect(
            self.browseTasksWidget,
            QtCore.SIGNAL('clickedIdSignal(QString)'),
            self.exportAssetOptionsWidget.updateView
        )

        QtCore.QObject.connect(
            self.browseTasksWidget,
            QtCore.SIGNAL('clickedIdSignal(QString)'),
            self.exportAssetOptionsWidget.updateTasks
        )

        QtCore.QObject.connect(
            self.exportAssetOptionsWidget,
            QtCore.SIGNAL('clickedAssetTypeSignal(QString)'),
            self.exportOptionsWidget.setStackedWidget
        )

        QtCore.QObject.connect(
            self.exportOptionsWidget.ui.publishButton,
            QtCore.SIGNAL('clicked()'),
            self.publishAsset
        )

        QtCore.QObject.connect(
            panelComInstance,
            QtCore.SIGNAL('publishProgressSignal(int)'),
            self.exportOptionsWidget.setProgress
        )

        self.browseTasksWidget.update()

    def resetOptions(self):
        self.exportOptionsWidget.resetOptions()
        self.exportAssetOptionsWidget.setAssetType(self.assetType)
        self.exportAssetOptionsWidget.setAssetName(self.assetName)
        self.exportOptionsWidget.setComment('')
        self.exportOptionsWidget.ui.thumbnailLineEdit.setText('')

        taskid = os.environ['FTRACK_TASKID']
        self.exportAssetOptionsWidget.updateTasks(ftrackId=taskid)
        self.exportAssetOptionsWidget.updateView(ftrackId=taskid)

    def setAssetType(self, assetType):
        self.exportAssetOptionsWidget.setAssetType(assetType)
        self.assetType = assetType

    def setAssetName(self, assetName):
        self.exportAssetOptionsWidget.setAssetName(assetName)
        self.assetName = assetName

    def setComment(self, comment):
        self.exportOptionsWidget.setComment(comment)

    def publishAsset(self):
        taskId = self.exportAssetOptionsWidget.getTaskId()
        shotid = self.exportAssetOptionsWidget.getShotId()

        assettype = self.exportAssetOptionsWidget.getAssetType()
        assetName = self.exportAssetOptionsWidget.getAssetName()
        status = self.exportAssetOptionsWidget.getStatus()
        print 'STATUS', status

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
        asset = ftrack.Task(shotid).createAsset(assetName, assettype)

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

    def keyPressEvent(self, e):
        if not e.key() == QtCore.Qt.Key_Escape:
            super(FtrackPublishAssetDialog, self).keyPressEvent(e)

    def getShotPath(self, shot):
        shotparents = shot.getParents()
        shotpath = ''

        for parent in reversed(shotparents):
            shotpath += parent.getName() + '.'
        shotpath += shot.getName()
        return shotpath

    def showWarning(self, subject, message):
        self.headerWidget.setMessage(message, 'warning')
