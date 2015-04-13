from PySide import QtGui
from ftrack_connect.ui.widget.info import FtrackInfoDialog


class FtrackMayaInfoDialog(FtrackInfoDialog):
    def __init__(self, parent=None, connector=None):
        super(FtrackMayaInfoDialog, self).__init__(
            parent=parent,
            connector=connector
        )

        self.headerWidget.setSizePolicy(
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Fixed
        )

    def keyPressEvent(self, e):
        if not e.key() == QtCore.Qt.Key_Escape:
            super(FtrackMayaInfoDialog, self).keyPressEvent(e)
