import getpass
from PySide import QtGui

from ftrack_connect.ui.widget.web_view import WebViewWidget
from ftrack_connect.ui.widget.header import Header
from ftrack_connect.ui.theme import applyTheme

import ftrack


class FtrackTasksDialog(QtGui.QDialog):
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
        super(FtrackTasksDialog, self).__init__(self.parent)
        applyTheme(self, 'integration')
        self.setSizePolicy(
            QtGui.QSizePolicy(
                QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Expanding
            )
        )
        self.setMinimumWidth(500)
        self.centralwidget = QtGui.QWidget(self)
        self.verticalMainLayout = QtGui.QVBoxLayout(self)
        self.horizontalLayout = QtGui.QHBoxLayout()

        self.headerWidget = Header(getpass.getuser(), self)
        self.headerWidget.setSizePolicy(
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Fixed
        )
        self.verticalMainLayout.addWidget(self.headerWidget)

        self.tasksWidget = WebViewWidget(self)

        url = ftrack.getWebWidgetUrl('tasks', theme='tf')

        self.tasksWidget.setUrl(url)
        self.horizontalLayout.addWidget(self.tasksWidget)
        self.verticalMainLayout.addLayout(self.horizontalLayout)

        self.setObjectName('ftrackTasks')
        self.setWindowTitle("ftrackTasks")
