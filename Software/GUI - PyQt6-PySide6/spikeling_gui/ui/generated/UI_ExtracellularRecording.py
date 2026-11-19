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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QHBoxLayout,
    QLabel, QLineEdit, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpacerItem, QTabWidget, QVBoxLayout,
    QWidget)

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
        self.processingTab = QWidget()
        self.processingTab.setObjectName(u"processingTab")
        self.processingTabLayout = QVBoxLayout(self.processingTab)
        self.processingTabLayout.setObjectName(u"processingTabLayout")
        self.analysisSelection = QLabel(self.processingTab)
        self.analysisSelection.setObjectName(u"analysisSelection")
        self.analysisSelection.setWordWrap(True)
        self.analysisSelection.setTextFormat(Qt.TextFormat.PlainText)

        self.processingTabLayout.addWidget(self.analysisSelection)

        self.analysisStatus = QLabel(self.processingTab)
        self.analysisStatus.setObjectName(u"analysisStatus")
        self.analysisStatus.setWordWrap(True)
        self.analysisStatus.setTextFormat(Qt.TextFormat.PlainText)

        self.processingTabLayout.addWidget(self.analysisStatus)

        self.referenceRow = QHBoxLayout()
        self.referenceRow.setObjectName(u"referenceRow")
        self.referenceLabel = QLabel(self.processingTab)
        self.referenceLabel.setObjectName(u"referenceLabel")

        self.referenceRow.addWidget(self.referenceLabel)

        self.referenceCombo = QComboBox(self.processingTab)
        self.referenceCombo.addItem("")
        self.referenceCombo.addItem("")
        self.referenceCombo.setObjectName(u"referenceCombo")

        self.referenceRow.addWidget(self.referenceCombo)

        self.refContactsLabel = QLabel(self.processingTab)
        self.refContactsLabel.setObjectName(u"refContactsLabel")

        self.referenceRow.addWidget(self.refContactsLabel)

        self.reference1 = QCheckBox(self.processingTab)
        self.reference1.setObjectName(u"reference1")
        self.reference1.setChecked(True)

        self.referenceRow.addWidget(self.reference1)

        self.reference2 = QCheckBox(self.processingTab)
        self.reference2.setObjectName(u"reference2")
        self.reference2.setChecked(True)

        self.referenceRow.addWidget(self.reference2)

        self.reference3 = QCheckBox(self.processingTab)
        self.reference3.setObjectName(u"reference3")
        self.reference3.setChecked(True)

        self.referenceRow.addWidget(self.reference3)

        self.reference4 = QCheckBox(self.processingTab)
        self.reference4.setObjectName(u"reference4")
        self.reference4.setChecked(True)

        self.referenceRow.addWidget(self.reference4)

        self.referenceRowSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.referenceRow.addItem(self.referenceRowSpacer)


        self.processingTabLayout.addLayout(self.referenceRow)

        self.bandpassRow = QHBoxLayout()
        self.bandpassRow.setObjectName(u"bandpassRow")
        self.bandpassCheck = QCheckBox(self.processingTab)
        self.bandpassCheck.setObjectName(u"bandpassCheck")
        self.bandpassCheck.setChecked(True)

        self.bandpassRow.addWidget(self.bandpassCheck)

        self.lowEditLabel = QLabel(self.processingTab)
        self.lowEditLabel.setObjectName(u"lowEditLabel")

        self.bandpassRow.addWidget(self.lowEditLabel)

        self.lowEdit = QLineEdit(self.processingTab)
        self.lowEdit.setObjectName(u"lowEdit")
        self.lowEdit.setText(u"300")
        self.lowEdit.setMaximumWidth(82)

        self.bandpassRow.addWidget(self.lowEdit)

        self.highEditLabel = QLabel(self.processingTab)
        self.highEditLabel.setObjectName(u"highEditLabel")

        self.bandpassRow.addWidget(self.highEditLabel)

        self.highEdit = QLineEdit(self.processingTab)
        self.highEdit.setObjectName(u"highEdit")
        self.highEdit.setText(u"3000")
        self.highEdit.setMaximumWidth(82)

        self.bandpassRow.addWidget(self.highEdit)

        self.bandpassRowSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.bandpassRow.addItem(self.bandpassRowSpacer)


        self.processingTabLayout.addLayout(self.bandpassRow)

        self.detectorRow = QHBoxLayout()
        self.detectorRow.setObjectName(u"detectorRow")
        self.thresholdEditLabel = QLabel(self.processingTab)
        self.thresholdEditLabel.setObjectName(u"thresholdEditLabel")

        self.detectorRow.addWidget(self.thresholdEditLabel)

        self.thresholdEdit = QLineEdit(self.processingTab)
        self.thresholdEdit.setObjectName(u"thresholdEdit")
        self.thresholdEdit.setText(u"-15")
        self.thresholdEdit.setMaximumWidth(82)

        self.detectorRow.addWidget(self.thresholdEdit)

        self.refractoryEditLabel = QLabel(self.processingTab)
        self.refractoryEditLabel.setObjectName(u"refractoryEditLabel")

        self.detectorRow.addWidget(self.refractoryEditLabel)

        self.refractoryEdit = QLineEdit(self.processingTab)
        self.refractoryEdit.setObjectName(u"refractoryEdit")
        self.refractoryEdit.setText(u"0.6")
        self.refractoryEdit.setMaximumWidth(82)

        self.detectorRow.addWidget(self.refractoryEdit)

        self.groupingEditLabel = QLabel(self.processingTab)
        self.groupingEditLabel.setObjectName(u"groupingEditLabel")

        self.detectorRow.addWidget(self.groupingEditLabel)

        self.groupingEdit = QLineEdit(self.processingTab)
        self.groupingEdit.setObjectName(u"groupingEdit")
        self.groupingEdit.setText(u"0.4")
        self.groupingEdit.setMaximumWidth(82)

        self.detectorRow.addWidget(self.groupingEdit)

        self.detectorRowSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.detectorRow.addItem(self.detectorRowSpacer)


        self.processingTabLayout.addLayout(self.detectorRow)

        self.detectionContactsRow = QHBoxLayout()
        self.detectionContactsRow.setObjectName(u"detectionContactsRow")
        self.detectionContactsLabel = QLabel(self.processingTab)
        self.detectionContactsLabel.setObjectName(u"detectionContactsLabel")

        self.detectionContactsRow.addWidget(self.detectionContactsLabel)

        self.detector1 = QCheckBox(self.processingTab)
        self.detector1.setObjectName(u"detector1")
        self.detector1.setChecked(True)

        self.detectionContactsRow.addWidget(self.detector1)

        self.detector2 = QCheckBox(self.processingTab)
        self.detector2.setObjectName(u"detector2")
        self.detector2.setChecked(True)

        self.detectionContactsRow.addWidget(self.detector2)

        self.detector3 = QCheckBox(self.processingTab)
        self.detector3.setObjectName(u"detector3")
        self.detector3.setChecked(True)

        self.detectionContactsRow.addWidget(self.detector3)

        self.detector4 = QCheckBox(self.processingTab)
        self.detector4.setObjectName(u"detector4")
        self.detector4.setChecked(True)

        self.detectionContactsRow.addWidget(self.detector4)

        self.runButton = QPushButton(self.processingTab)
        self.runButton.setObjectName(u"runButton")

        self.detectionContactsRow.addWidget(self.runButton)

        self.pinButton = QPushButton(self.processingTab)
        self.pinButton.setObjectName(u"pinButton")

        self.detectionContactsRow.addWidget(self.pinButton)

        self.detectionContactsRowSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.detectionContactsRow.addItem(self.detectionContactsRowSpacer)


        self.processingTabLayout.addLayout(self.detectionContactsRow)

        self.analysisPlotHost = QWidget(self.processingTab)
        self.analysisPlotHost.setObjectName(u"analysisPlotHost")
        self.analysisPlotLayout = QVBoxLayout(self.analysisPlotHost)
        self.analysisPlotLayout.setObjectName(u"analysisPlotLayout")
        self.analysisPlotLayout.setContentsMargins(0, 0, 0, 0)

        self.processingTabLayout.addWidget(self.analysisPlotHost)

        self.tabs.addTab(self.processingTab, "")
        self.comparisonTab = QWidget()
        self.comparisonTab.setObjectName(u"comparisonTab")
        self.comparisonTabLayout = QVBoxLayout(self.comparisonTab)
        self.comparisonTabLayout.setObjectName(u"comparisonTabLayout")
        self.waveWindowRow = QHBoxLayout()
        self.waveWindowRow.setObjectName(u"waveWindowRow")
        self.preEditLabel = QLabel(self.comparisonTab)
        self.preEditLabel.setObjectName(u"preEditLabel")

        self.waveWindowRow.addWidget(self.preEditLabel)

        self.preEdit = QLineEdit(self.comparisonTab)
        self.preEdit.setObjectName(u"preEdit")
        self.preEdit.setText(u"1")
        self.preEdit.setMaximumWidth(82)

        self.waveWindowRow.addWidget(self.preEdit)

        self.postEditLabel = QLabel(self.comparisonTab)
        self.postEditLabel.setObjectName(u"postEditLabel")

        self.waveWindowRow.addWidget(self.postEditLabel)

        self.postEdit = QLineEdit(self.comparisonTab)
        self.postEdit.setObjectName(u"postEdit")
        self.postEdit.setText(u"2")
        self.postEdit.setMaximumWidth(82)

        self.waveWindowRow.addWidget(self.postEdit)

        self.snippetEditLabel = QLabel(self.comparisonTab)
        self.snippetEditLabel.setObjectName(u"snippetEditLabel")

        self.waveWindowRow.addWidget(self.snippetEditLabel)

        self.snippetEdit = QLineEdit(self.comparisonTab)
        self.snippetEdit.setObjectName(u"snippetEdit")
        self.snippetEdit.setText(u"16")
        self.snippetEdit.setMaximumWidth(82)

        self.waveWindowRow.addWidget(self.snippetEdit)

        self.waveWindowRowSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.waveWindowRow.addItem(self.waveWindowRowSpacer)


        self.comparisonTabLayout.addLayout(self.waveWindowRow)

        self.waveSelectionRow = QHBoxLayout()
        self.waveSelectionRow.setObjectName(u"waveSelectionRow")
        self.firstGroupEditLabel = QLabel(self.comparisonTab)
        self.firstGroupEditLabel.setObjectName(u"firstGroupEditLabel")

        self.waveSelectionRow.addWidget(self.firstGroupEditLabel)

        self.firstGroupEdit = QLineEdit(self.comparisonTab)
        self.firstGroupEdit.setObjectName(u"firstGroupEdit")
        self.firstGroupEdit.setText(u"1")
        self.firstGroupEdit.setMaximumWidth(82)

        self.waveSelectionRow.addWidget(self.firstGroupEdit)

        self.groupCountEditLabel = QLabel(self.comparisonTab)
        self.groupCountEditLabel.setObjectName(u"groupCountEditLabel")

        self.waveSelectionRow.addWidget(self.groupCountEditLabel)

        self.groupCountEdit = QLineEdit(self.comparisonTab)
        self.groupCountEdit.setObjectName(u"groupCountEdit")
        self.groupCountEdit.setText(u"")
        self.groupCountEdit.setMaximumWidth(82)

        self.waveSelectionRow.addWidget(self.groupCountEdit)

        self.rerunButton = QPushButton(self.comparisonTab)
        self.rerunButton.setObjectName(u"rerunButton")

        self.waveSelectionRow.addWidget(self.rerunButton)

        self.waveSelectionRowSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.waveSelectionRow.addItem(self.waveSelectionRowSpacer)


        self.comparisonTabLayout.addLayout(self.waveSelectionRow)

        self.sourceComparisonRow = QHBoxLayout()
        self.sourceComparisonRow.setObjectName(u"sourceComparisonRow")
        self.sourceLabel = QLabel(self.comparisonTab)
        self.sourceLabel.setObjectName(u"sourceLabel")

        self.sourceComparisonRow.addWidget(self.sourceLabel)

        self.sourceCombo = QComboBox(self.comparisonTab)
        self.sourceCombo.setObjectName(u"sourceCombo")

        self.sourceComparisonRow.addWidget(self.sourceCombo)

        self.toleranceEditLabel = QLabel(self.comparisonTab)
        self.toleranceEditLabel.setObjectName(u"toleranceEditLabel")

        self.sourceComparisonRow.addWidget(self.toleranceEditLabel)

        self.toleranceEdit = QLineEdit(self.comparisonTab)
        self.toleranceEdit.setObjectName(u"toleranceEdit")
        self.toleranceEdit.setText(u"2")
        self.toleranceEdit.setMaximumWidth(82)

        self.sourceComparisonRow.addWidget(self.toleranceEdit)

        self.matchButton = QPushButton(self.comparisonTab)
        self.matchButton.setObjectName(u"matchButton")

        self.sourceComparisonRow.addWidget(self.matchButton)

        self.analysisExportButton = QPushButton(self.comparisonTab)
        self.analysisExportButton.setObjectName(u"analysisExportButton")

        self.sourceComparisonRow.addWidget(self.analysisExportButton)

        self.sourceComparisonRowSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.sourceComparisonRow.addItem(self.sourceComparisonRowSpacer)


        self.comparisonTabLayout.addLayout(self.sourceComparisonRow)

        self.comparisonStatus = QLabel(self.comparisonTab)
        self.comparisonStatus.setObjectName(u"comparisonStatus")
        self.comparisonStatus.setWordWrap(True)
        self.comparisonStatus.setTextFormat(Qt.TextFormat.PlainText)

        self.comparisonTabLayout.addWidget(self.comparisonStatus)

        self.comparisonDetails = QPlainTextEdit(self.comparisonTab)
        self.comparisonDetails.setObjectName(u"comparisonDetails")
        self.comparisonDetails.setReadOnly(True)
        self.comparisonDetails.setMaximumHeight(115)

        self.comparisonTabLayout.addWidget(self.comparisonDetails)

        self.waveformPlotHost = QWidget(self.comparisonTab)
        self.waveformPlotHost.setObjectName(u"waveformPlotHost")
        self.waveformPlotLayout = QVBoxLayout(self.waveformPlotHost)
        self.waveformPlotLayout.setObjectName(u"waveformPlotLayout")
        self.waveformPlotLayout.setContentsMargins(0, 0, 0, 0)

        self.comparisonTabLayout.addWidget(self.waveformPlotHost)

        self.tabs.addTab(self.comparisonTab, "")

        self.rootLayout.addWidget(self.tabs)

#if QT_CONFIG(shortcut)
        self.stageLabel.setBuddy(self.stageCombo)
        self.indexLabel.setBuddy(self.indexEdit)
        self.countLabel.setBuddy(self.countEdit)
        self.referenceLabel.setBuddy(self.referenceCombo)
        self.lowEditLabel.setBuddy(self.lowEdit)
        self.highEditLabel.setBuddy(self.highEdit)
        self.thresholdEditLabel.setBuddy(self.thresholdEdit)
        self.refractoryEditLabel.setBuddy(self.refractoryEdit)
        self.groupingEditLabel.setBuddy(self.groupingEdit)
        self.preEditLabel.setBuddy(self.preEdit)
        self.postEditLabel.setBuddy(self.postEdit)
        self.snippetEditLabel.setBuddy(self.snippetEdit)
        self.firstGroupEditLabel.setBuddy(self.firstGroupEdit)
        self.groupCountEditLabel.setBuddy(self.groupCountEdit)
        self.sourceLabel.setBuddy(self.sourceCombo)
        self.toleranceEditLabel.setBuddy(self.toleranceEdit)
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
        self.referenceLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Reference", None))
        self.referenceCombo.setItemText(0, QCoreApplication.translate("ExtracellularRecording", u"None", None))
        self.referenceCombo.setItemText(1, QCoreApplication.translate("ExtracellularRecording", u"Common average (CAR)", None))

#if QT_CONFIG(tooltip)
        self.referenceCombo.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"The selected contacts contribute to the mean subtracted from all four signals. Shared neuronal evidence can cancel.", None))
#endif // QT_CONFIG(tooltip)
        self.refContactsLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Contacts in average", None))
        self.reference1.setText(QCoreApplication.translate("ExtracellularRecording", u"E1", None))
        self.reference2.setText(QCoreApplication.translate("ExtracellularRecording", u"E2", None))
        self.reference3.setText(QCoreApplication.translate("ExtracellularRecording", u"E3", None))
        self.reference4.setText(QCoreApplication.translate("ExtracellularRecording", u"E4", None))
#if QT_CONFIG(tooltip)
        self.bandpassCheck.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"Filter a fresh copy of the saved broadband. Warm-up rows after each reset are excluded from detection.", None))
#endif // QT_CONFIG(tooltip)
        self.bandpassCheck.setText(QCoreApplication.translate("ExtracellularRecording", u"Causal bandpass", None))
        self.lowEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Low (Hz)", None))
        self.highEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"High (Hz)", None))
        self.thresholdEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Negative threshold (\u00b5V)", None))
        self.refractoryEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Refractory (ms)", None))
        self.groupingEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Grouping (ms)", None))
#if QT_CONFIG(tooltip)
        self.groupingEdit.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"The grouping window starts at the first accepted crossing. A crossing at exact expiry starts a new group.", None))
#endif // QT_CONFIG(tooltip)
        self.detectionContactsLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Detection contacts", None))
        self.detector1.setText(QCoreApplication.translate("ExtracellularRecording", u"E1", None))
        self.detector2.setText(QCoreApplication.translate("ExtracellularRecording", u"E2", None))
        self.detector3.setText(QCoreApplication.translate("ExtracellularRecording", u"E3", None))
        self.detector4.setText(QCoreApplication.translate("ExtracellularRecording", u"E4", None))
        self.runButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Run analysis B", None))
        self.pinButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Set B as reference A", None))
        self.tabs.setTabText(self.tabs.indexOf(self.processingTab), QCoreApplication.translate("ExtracellularRecording", u"Processing & Detection", None))
        self.preEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Pre-event (ms)", None))
        self.postEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Post-event (ms)", None))
        self.snippetEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Overlays", None))
        self.firstGroupEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"First group", None))
        self.groupCountEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Group count", None))
        self.groupCountEdit.setPlaceholderText(QCoreApplication.translate("ExtracellularRecording", u"All remaining", None))
        self.rerunButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Run analysis B", None))
        self.sourceLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Source evidence", None))
        self.toleranceEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Match tolerance (ms)", None))
        self.matchButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Refresh agreement", None))
        self.analysisExportButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Export analysis\u2026", None))
        self.tabs.setTabText(self.tabs.indexOf(self.comparisonTab), QCoreApplication.translate("ExtracellularRecording", u"Waveforms & Comparison", None))
        pass
    # retranslateUi
