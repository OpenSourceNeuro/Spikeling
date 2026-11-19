# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'UI_ExtracellularRecording.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QSizePolicy,
    QTabWidget, QVBoxLayout, QWidget)

class Ui_ExtracellularRecording(object):
    def setupUi(self, ExtracellularRecording):
        if not ExtracellularRecording.objectName():
            ExtracellularRecording.setObjectName(u"ExtracellularRecording")
        self.rootLayout = QVBoxLayout(ExtracellularRecording)
        self.rootLayout.setObjectName(u"rootLayout")
        self.tabs = QTabWidget(ExtracellularRecording)
        self.tabs.setObjectName(u"tabs")
        self.recording = QWidget()
        self.recording.setObjectName(u"recording")
        self.recordingLayout = QVBoxLayout(self.recording)
        self.recordingLayout.setObjectName(u"recordingLayout")
        self.openLayout = QHBoxLayout()
        self.openLayout.setObjectName(u"openLayout")
        self.openButton = QPushButton(self.recording)
        self.openButton.setObjectName(u"openButton")

        self.openLayout.addWidget(self.openButton)

        self.statusLabel = QLabel(self.recording)
        self.statusLabel.setObjectName(u"statusLabel")
        self.statusLabel.setWordWrap(True)
        self.statusLabel.setTextFormat(Qt.TextFormat.PlainText)
        self.statusLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.openLayout.addWidget(self.statusLabel)


        self.recordingLayout.addLayout(self.openLayout)

        self.metadata = QPlainTextEdit(self.recording)
        self.metadata.setObjectName(u"metadata")
        self.metadata.setReadOnly(True)
        self.metadata.setMaximumHeight(155)

        self.recordingLayout.addWidget(self.metadata)

        self.intervalLayout = QHBoxLayout()
        self.intervalLayout.setObjectName(u"intervalLayout")
        self.stageLabel = QLabel(self.recording)
        self.stageLabel.setObjectName(u"stageLabel")

        self.intervalLayout.addWidget(self.stageLabel)

        self.stageCombo = QComboBox(self.recording)
        self.stageCombo.setObjectName(u"stageCombo")

        self.intervalLayout.addWidget(self.stageCombo)

        self.indexLabel = QLabel(self.recording)
        self.indexLabel.setObjectName(u"indexLabel")

        self.intervalLayout.addWidget(self.indexLabel)

        self.indexEdit = QLineEdit(self.recording)
        self.indexEdit.setObjectName(u"indexEdit")
        self.indexEdit.setText(u"0")

        self.intervalLayout.addWidget(self.indexEdit)

        self.countLabel = QLabel(self.recording)
        self.countLabel.setObjectName(u"countLabel")

        self.intervalLayout.addWidget(self.countLabel)

        self.countEdit = QLineEdit(self.recording)
        self.countEdit.setObjectName(u"countEdit")
        self.countEdit.setText(u"10000")

        self.intervalLayout.addWidget(self.countEdit)

        self.previewButton = QPushButton(self.recording)
        self.previewButton.setObjectName(u"previewButton")

        self.intervalLayout.addWidget(self.previewButton)

        self.exportButton = QPushButton(self.recording)
        self.exportButton.setObjectName(u"exportButton")

        self.intervalLayout.addWidget(self.exportButton)


        self.recordingLayout.addLayout(self.intervalLayout)

        self.plotHost = QWidget(self.recording)
        self.plotHost.setObjectName(u"plotHost")
        self.plotLayout = QVBoxLayout(self.plotHost)
        self.plotLayout.setObjectName(u"plotLayout")
        self.plotLayout.setContentsMargins(0, 0, 0, 0)

        self.recordingLayout.addWidget(self.plotHost)

        self.tabs.addTab(self.recording, "")

        self.rootLayout.addWidget(self.tabs)

#if QT_CONFIG(shortcut)
        self.stageLabel.setBuddy(self.stageCombo)
        self.indexLabel.setBuddy(self.indexEdit)
        self.countLabel.setBuddy(self.countEdit)
#endif // QT_CONFIG(shortcut)

        self.retranslateUi(ExtracellularRecording)

        QMetaObject.connectSlotsByName(ExtracellularRecording)
    # setupUi

    def retranslateUi(self, ExtracellularRecording):
        self.openButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Open recording\u2026", None))
        self.statusLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Open a session manifest or an extracellular CSV.", None))
        self.metadata.setPlaceholderText(QCoreApplication.translate("ExtracellularRecording", u"Recording metadata", None))
        self.stageLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Signal", None))
        self.indexLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"First accepted index", None))
        self.countLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Rows", None))
        self.previewButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Preview", None))
        self.exportButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Export CSV\u2026", None))
        self.tabs.setTabText(self.tabs.indexOf(self.recording), QCoreApplication.translate("ExtracellularRecording", u"Recording", None))
        pass
    # retranslateUi
