# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'UI_ExtracellularRecording.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QFrame, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QSizePolicy,
    QSpacerItem, QStackedWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

class Ui_ExtracellularRecording(object):
    def setupUi(self, ExtracellularRecording):
        if not ExtracellularRecording.objectName():
            ExtracellularRecording.setObjectName(u"ExtracellularRecording")
        ExtracellularRecording.setStyleSheet(u"QPushButton {\n"
"    background: #073642;\n"
"    color: #BECDCD;\n"
"    border: 1px solid #586E75;\n"
"    border-radius: 5px;\n"
"    padding: 5px 9px;\n"
"}\n"
"QPushButton:hover {\n"
"    border-color: #268BD2;\n"
"}\n"
"QPushButton:focus {\n"
"    border: 2px solid #268BD2;\n"
"}\n"
"QPushButton:disabled {\n"
"    color: #586E75;\n"
"    border-color: #073642;\n"
"}\n"
"QLineEdit, QComboBox, QPlainTextEdit {\n"
"    background: #073642;\n"
"    color: #BECDCD;\n"
"    border: 1px solid #586E75;\n"
"    border-radius: 5px;\n"
"    padding: 4px 7px;\n"
"}\n"
"QLineEdit:focus, QComboBox:focus {\n"
"    border: 2px solid #268BD2;\n"
"}\n"
"QTableWidget { background: #002B36; color: #BECDCD; gridline-color: #073642; }\n"
"QLabel#recordingGuide, QLabel#processingGuide, QLabel#detectionGuide, QLabel#spectrumGuide {\n"
"    font-size: 10pt;\n"
"}\n"
"QPushButton[analysisTab=\"true\"] {\n"
"    color: #586E75;\n"
"    background: transparent;\n"
"    border: 0;\n"
"    border-bottom: 2px solid transparent;\n"
" "
                        "   padding: 5px 10px;\n"
"}\n"
"QPushButton[analysisTab=\"true\"]:checked {\n"
"    color: #268BD2;\n"
"    border-bottom: 2px solid #268BD2;\n"
"}\n"
"QPushButton[analysisTab=\"true\"]:hover, QPushButton[analysisTab=\"true\"]:focus {\n"
"    background: #073642;\n"
"}\n"
"QFrame[analysisPanel=\"true\"] {\n"
"    background: #002B36;\n"
"    border: 1px solid #073642;\n"
"    border-radius: 8px;\n"
"}\n"
"QLabel[analysisStatus=\"true\"] {\n"
"    color: #586E75;\n"
"}\n"
"")
        self.rootLayout = QVBoxLayout(ExtracellularRecording)
        self.rootLayout.setSpacing(6)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(5, 5, 5, 5)
        self.analysisHeading = QLabel(ExtracellularRecording)
        self.analysisHeading.setObjectName(u"analysisHeading")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.analysisHeading.setFont(font)

        self.rootLayout.addWidget(self.analysisHeading)

        self.analysisNavigation = QHBoxLayout()
        self.analysisNavigation.setSpacing(6)
        self.analysisNavigation.setObjectName(u"analysisNavigation")
        self.analysisNavigation.setContentsMargins(0, 0, 0, 0)
        self.navRecording = QPushButton(ExtracellularRecording)
        self.navRecording.setObjectName(u"navRecording")
        self.navRecording.setChecked(True)
        self.navRecording.setMinimumSize(QSize(100, 34))
        font1 = QFont()
        font1.setPointSize(12)
        font1.setBold(True)
        self.navRecording.setFont(font1)
        self.navRecording.setCheckable(True)
        self.navRecording.setProperty(u"analysisTab", True)

        self.analysisNavigation.addWidget(self.navRecording)

        self.navProcessing = QPushButton(ExtracellularRecording)
        self.navProcessing.setObjectName(u"navProcessing")
        self.navProcessing.setChecked(False)
        self.navProcessing.setMinimumSize(QSize(100, 34))
        self.navProcessing.setFont(font1)
        self.navProcessing.setCheckable(True)
        self.navProcessing.setProperty(u"analysisTab", True)

        self.analysisNavigation.addWidget(self.navProcessing)

        self.navDetection = QPushButton(ExtracellularRecording)
        self.navDetection.setObjectName(u"navDetection")
        self.navDetection.setChecked(False)
        self.navDetection.setMinimumSize(QSize(100, 34))
        self.navDetection.setFont(font1)
        self.navDetection.setCheckable(True)
        self.navDetection.setProperty(u"analysisTab", True)

        self.analysisNavigation.addWidget(self.navDetection)

        self.navWaveforms = QPushButton(ExtracellularRecording)
        self.navWaveforms.setObjectName(u"navWaveforms")
        self.navWaveforms.setChecked(False)
        self.navWaveforms.setMinimumSize(QSize(100, 34))
        self.navWaveforms.setFont(font1)
        self.navWaveforms.setCheckable(True)
        self.navWaveforms.setProperty(u"analysisTab", True)

        self.analysisNavigation.addWidget(self.navWaveforms)

        self.navComparison = QPushButton(ExtracellularRecording)
        self.navComparison.setObjectName(u"navComparison")
        self.navComparison.setChecked(False)
        self.navComparison.setMinimumSize(QSize(100, 34))
        self.navComparison.setFont(font1)
        self.navComparison.setCheckable(True)
        self.navComparison.setProperty(u"analysisTab", True)

        self.analysisNavigation.addWidget(self.navComparison)

        self.navSpectrum = QPushButton(ExtracellularRecording)
        self.navSpectrum.setObjectName(u"navSpectrum")
        self.navSpectrum.setChecked(False)
        self.navSpectrum.setMinimumSize(QSize(100, 34))
        self.navSpectrum.setFont(font1)
        self.navSpectrum.setCheckable(True)
        self.navSpectrum.setProperty(u"analysisTab", True)

        self.analysisNavigation.addWidget(self.navSpectrum)

        self.analysisNavSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.analysisNavigation.addItem(self.analysisNavSpacer)


        self.rootLayout.addLayout(self.analysisNavigation)

        self.pageStack = QStackedWidget(ExtracellularRecording)
        self.pageStack.setObjectName(u"pageStack")
        self.recording = QWidget()
        self.recording.setObjectName(u"recording")
        self.recordingLayout = QVBoxLayout(self.recording)
        self.recordingLayout.setSpacing(6)
        self.recordingLayout.setObjectName(u"recordingLayout")
        self.recordingLayout.setContentsMargins(8, 8, 8, 8)
        self.recordingStack = QStackedWidget(self.recording)
        self.recordingStack.setObjectName(u"recordingStack")
        self.recordingOverview = QWidget()
        self.recordingOverview.setObjectName(u"recordingOverview")
        self.recordingOverviewLayout = QVBoxLayout(self.recordingOverview)
        self.recordingOverviewLayout.setObjectName(u"recordingOverviewLayout")
        self.recordingOverviewLayout.setContentsMargins(0, 0, 0, 0)
        self.recordingControls = QFrame(self.recordingOverview)
        self.recordingControls.setObjectName(u"recordingControls")
        self.recordingControls.setProperty(u"analysisPanel", True)
        self.recordingControlsLayout = QVBoxLayout(self.recordingControls)
        self.recordingControlsLayout.setSpacing(5)
        self.recordingControlsLayout.setObjectName(u"recordingControlsLayout")
        self.recordingControlsLayout.setContentsMargins(8, 8, 8, 8)
        self.openLayout = QHBoxLayout()
        self.openLayout.setObjectName(u"openLayout")
        self.openButton = QPushButton(self.recordingControls)
        self.openButton.setObjectName(u"openButton")
        font2 = QFont()
        font2.setPointSize(10)
        font2.setBold(True)
        self.openButton.setFont(font2)

        self.openLayout.addWidget(self.openButton)

        self.metadataButton = QPushButton(self.recordingControls)
        self.metadataButton.setObjectName(u"metadataButton")
        self.metadataButton.setEnabled(False)
        self.metadataButton.setFont(font2)

        self.openLayout.addWidget(self.metadataButton)

        self.statusLabel = QLabel(self.recordingControls)
        self.statusLabel.setObjectName(u"statusLabel")
        self.statusLabel.setWordWrap(True)
        self.statusLabel.setTextFormat(Qt.TextFormat.PlainText)
        self.statusLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.statusLabel.sizePolicy().hasHeightForWidth())
        self.statusLabel.setSizePolicy(sizePolicy)

        self.openLayout.addWidget(self.statusLabel)


        self.recordingControlsLayout.addLayout(self.openLayout)

        self.intervalLayout = QHBoxLayout()
        self.intervalLayout.setObjectName(u"intervalLayout")
        self.stageLabel = QLabel(self.recordingControls)
        self.stageLabel.setObjectName(u"stageLabel")

        self.intervalLayout.addWidget(self.stageLabel)

        self.stageCombo = QComboBox(self.recordingControls)
        self.stageCombo.setObjectName(u"stageCombo")
        self.stageCombo.setMinimumWidth(160)

        self.intervalLayout.addWidget(self.stageCombo)

        self.indexLabel = QLabel(self.recordingControls)
        self.indexLabel.setObjectName(u"indexLabel")

        self.intervalLayout.addWidget(self.indexLabel)

        self.indexEdit = QLineEdit(self.recordingControls)
        self.indexEdit.setObjectName(u"indexEdit")
        self.indexEdit.setMaximumWidth(85)
        self.indexEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.indexEdit.setText(u"0")

        self.intervalLayout.addWidget(self.indexEdit)

        self.intervalLayoutSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.intervalLayout.addItem(self.intervalLayoutSpacer)


        self.recordingControlsLayout.addLayout(self.intervalLayout)

        self.sampleIntervalRow = QHBoxLayout()
        self.sampleIntervalRow.setObjectName(u"sampleIntervalRow")
        self.countLabel = QLabel(self.recordingControls)
        self.countLabel.setObjectName(u"countLabel")

        self.sampleIntervalRow.addWidget(self.countLabel)

        self.countEdit = QLineEdit(self.recordingControls)
        self.countEdit.setObjectName(u"countEdit")
        self.countEdit.setMaximumWidth(85)
        self.countEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countEdit.setText(u"10000")

        self.sampleIntervalRow.addWidget(self.countEdit)

        self.previewButton = QPushButton(self.recordingControls)
        self.previewButton.setObjectName(u"previewButton")
        self.previewButton.setFont(font2)

        self.sampleIntervalRow.addWidget(self.previewButton)

        self.exportButton = QPushButton(self.recordingControls)
        self.exportButton.setObjectName(u"exportButton")
        self.exportButton.setFont(font2)

        self.sampleIntervalRow.addWidget(self.exportButton)

        self.sampleIntervalRowSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.sampleIntervalRow.addItem(self.sampleIntervalRowSpacer)


        self.recordingControlsLayout.addLayout(self.sampleIntervalRow)

        self.recordingGuide = QLabel(self.recordingControls)
        self.recordingGuide.setObjectName(u"recordingGuide")
        self.recordingGuide.setWordWrap(True)

        self.recordingControlsLayout.addWidget(self.recordingGuide)


        self.recordingOverviewLayout.addWidget(self.recordingControls)

        self.plotHost = QFrame(self.recordingOverview)
        self.plotHost.setObjectName(u"plotHost")
        self.plotHost.setProperty(u"analysisPanel", True)
        self.plotLayout = QVBoxLayout(self.plotHost)
        self.plotLayout.setObjectName(u"plotLayout")
        self.plotLayout.setContentsMargins(3, 3, 3, 3)

        self.recordingOverviewLayout.addWidget(self.plotHost)

        self.recordingOverviewLayout.setStretch(1, 1)
        self.recordingStack.addWidget(self.recordingOverview)
        self.recordingMetadata = QWidget()
        self.recordingMetadata.setObjectName(u"recordingMetadata")
        self.recordingMetadataLayout = QVBoxLayout(self.recordingMetadata)
        self.recordingMetadataLayout.setObjectName(u"recordingMetadataLayout")
        self.metadataToolbar = QHBoxLayout()
        self.metadataToolbar.setObjectName(u"metadataToolbar")
        self.metadataBackButton = QPushButton(self.recordingMetadata)
        self.metadataBackButton.setObjectName(u"metadataBackButton")

        self.metadataToolbar.addWidget(self.metadataBackButton)

        self.metadataToolbarSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.metadataToolbar.addItem(self.metadataToolbarSpacer)


        self.recordingMetadataLayout.addLayout(self.metadataToolbar)

        self.metadata = QPlainTextEdit(self.recordingMetadata)
        self.metadata.setObjectName(u"metadata")
        self.metadata.setReadOnly(True)

        self.recordingMetadataLayout.addWidget(self.metadata)

        self.recordingStack.addWidget(self.recordingMetadata)

        self.recordingLayout.addWidget(self.recordingStack)

        self.pageStack.addWidget(self.recording)
        self.processingTab = QWidget()
        self.processingTab.setObjectName(u"processingTab")
        self.processingTabLayout = QVBoxLayout(self.processingTab)
        self.processingTabLayout.setSpacing(6)
        self.processingTabLayout.setObjectName(u"processingTabLayout")
        self.processingTabLayout.setContentsMargins(8, 8, 8, 8)
        self.processingControls = QFrame(self.processingTab)
        self.processingControls.setObjectName(u"processingControls")
        self.processingControls.setProperty(u"analysisPanel", True)
        self.processingControlsLayout = QVBoxLayout(self.processingControls)
        self.processingControlsLayout.setSpacing(5)
        self.processingControlsLayout.setObjectName(u"processingControlsLayout")
        self.processingControlsLayout.setContentsMargins(8, 8, 8, 8)
        self.referenceRow = QHBoxLayout()
        self.referenceRow.setObjectName(u"referenceRow")
        self.referenceLabel = QLabel(self.processingControls)
        self.referenceLabel.setObjectName(u"referenceLabel")

        self.referenceRow.addWidget(self.referenceLabel)

        self.referenceCombo = QComboBox(self.processingControls)
        self.referenceCombo.addItem("")
        self.referenceCombo.addItem("")
        self.referenceCombo.addItem("")
        self.referenceCombo.setObjectName(u"referenceCombo")

        self.referenceRow.addWidget(self.referenceCombo)

        self.refContactsLabel = QLabel(self.processingControls)
        self.refContactsLabel.setObjectName(u"refContactsLabel")

        self.referenceRow.addWidget(self.refContactsLabel)

        self.reference1 = QCheckBox(self.processingControls)
        self.reference1.setObjectName(u"reference1")
        self.reference1.setChecked(True)

        self.referenceRow.addWidget(self.reference1)

        self.reference2 = QCheckBox(self.processingControls)
        self.reference2.setObjectName(u"reference2")
        self.reference2.setChecked(True)

        self.referenceRow.addWidget(self.reference2)

        self.reference3 = QCheckBox(self.processingControls)
        self.reference3.setObjectName(u"reference3")
        self.reference3.setChecked(True)

        self.referenceRow.addWidget(self.reference3)

        self.reference4 = QCheckBox(self.processingControls)
        self.reference4.setObjectName(u"reference4")
        self.reference4.setChecked(True)

        self.referenceRow.addWidget(self.reference4)

        self.singleReferenceCombo = QComboBox(self.processingControls)
        self.singleReferenceCombo.addItem("")
        self.singleReferenceCombo.addItem("")
        self.singleReferenceCombo.addItem("")
        self.singleReferenceCombo.addItem("")
        self.singleReferenceCombo.setObjectName(u"singleReferenceCombo")

        self.referenceRow.addWidget(self.singleReferenceCombo)

        self.referenceRowSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.referenceRow.addItem(self.referenceRowSpacer)


        self.processingControlsLayout.addLayout(self.referenceRow)

        self.bandpassRow = QHBoxLayout()
        self.bandpassRow.setObjectName(u"bandpassRow")
        self.bandpassCheck = QCheckBox(self.processingControls)
        self.bandpassCheck.setObjectName(u"bandpassCheck")
        self.bandpassCheck.setChecked(True)

        self.bandpassRow.addWidget(self.bandpassCheck)

        self.lowEditLabel = QLabel(self.processingControls)
        self.lowEditLabel.setObjectName(u"lowEditLabel")

        self.bandpassRow.addWidget(self.lowEditLabel)

        self.lowEdit = QLineEdit(self.processingControls)
        self.lowEdit.setObjectName(u"lowEdit")
        self.lowEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lowEdit.setText(u"300")
        self.lowEdit.setMaximumWidth(85)

        self.bandpassRow.addWidget(self.lowEdit)

        self.highEditLabel = QLabel(self.processingControls)
        self.highEditLabel.setObjectName(u"highEditLabel")

        self.bandpassRow.addWidget(self.highEditLabel)

        self.highEdit = QLineEdit(self.processingControls)
        self.highEdit.setObjectName(u"highEdit")
        self.highEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.highEdit.setText(u"3000")
        self.highEdit.setMaximumWidth(85)

        self.bandpassRow.addWidget(self.highEdit)

        self.notchLabel = QLabel(self.processingControls)
        self.notchLabel.setObjectName(u"notchLabel")

        self.bandpassRow.addWidget(self.notchLabel)

        self.notchCombo = QComboBox(self.processingControls)
        self.notchCombo.addItem("")
        self.notchCombo.addItem("")
        self.notchCombo.addItem("")
        self.notchCombo.setObjectName(u"notchCombo")

        self.bandpassRow.addWidget(self.notchCombo)

        self.bandpassRowSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.bandpassRow.addItem(self.bandpassRowSpacer)


        self.processingControlsLayout.addLayout(self.bandpassRow)

        self.processingGuide = QLabel(self.processingControls)
        self.processingGuide.setObjectName(u"processingGuide")
        self.processingGuide.setWordWrap(True)

        self.processingControlsLayout.addWidget(self.processingGuide)


        self.processingTabLayout.addWidget(self.processingControls)

        self.analysisPlotHost = QFrame(self.processingTab)
        self.analysisPlotHost.setObjectName(u"analysisPlotHost")
        self.analysisPlotHost.setProperty(u"analysisPanel", True)
        self.analysisPlotLayout = QVBoxLayout(self.analysisPlotHost)
        self.analysisPlotLayout.setObjectName(u"analysisPlotLayout")
        self.analysisPlotLayout.setContentsMargins(3, 3, 3, 3)

        self.processingTabLayout.addWidget(self.analysisPlotHost)

        self.processingTabLayout.setStretch(1, 1)
        self.pageStack.addWidget(self.processingTab)
        self.detectionTab = QWidget()
        self.detectionTab.setObjectName(u"detectionTab")
        self.detectionTabLayout = QVBoxLayout(self.detectionTab)
        self.detectionTabLayout.setSpacing(6)
        self.detectionTabLayout.setObjectName(u"detectionTabLayout")
        self.detectionTabLayout.setContentsMargins(8, 8, 8, 8)
        self.detectionControls = QFrame(self.detectionTab)
        self.detectionControls.setObjectName(u"detectionControls")
        self.detectionControls.setProperty(u"analysisPanel", True)
        self.detectionControlsLayout = QVBoxLayout(self.detectionControls)
        self.detectionControlsLayout.setSpacing(5)
        self.detectionControlsLayout.setObjectName(u"detectionControlsLayout")
        self.detectionControlsLayout.setContentsMargins(8, 8, 8, 8)
        self.detectorRow = QHBoxLayout()
        self.detectorRow.setObjectName(u"detectorRow")
        self.polarityLabel = QLabel(self.detectionControls)
        self.polarityLabel.setObjectName(u"polarityLabel")

        self.detectorRow.addWidget(self.polarityLabel)

        self.polarityCombo = QComboBox(self.detectionControls)
        self.polarityCombo.addItem("")
        self.polarityCombo.addItem("")
        self.polarityCombo.addItem("")
        self.polarityCombo.setObjectName(u"polarityCombo")

        self.detectorRow.addWidget(self.polarityCombo)

        self.thresholdEditLabel = QLabel(self.detectionControls)
        self.thresholdEditLabel.setObjectName(u"thresholdEditLabel")

        self.detectorRow.addWidget(self.thresholdEditLabel)

        self.thresholdEdit = QLineEdit(self.detectionControls)
        self.thresholdEdit.setObjectName(u"thresholdEdit")
        self.thresholdEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thresholdEdit.setText(u"-15")
        self.thresholdEdit.setMaximumWidth(85)

        self.detectorRow.addWidget(self.thresholdEdit)

        self.refractoryEditLabel = QLabel(self.detectionControls)
        self.refractoryEditLabel.setObjectName(u"refractoryEditLabel")

        self.detectorRow.addWidget(self.refractoryEditLabel)

        self.refractoryEdit = QLineEdit(self.detectionControls)
        self.refractoryEdit.setObjectName(u"refractoryEdit")
        self.refractoryEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.refractoryEdit.setText(u"0.6")
        self.refractoryEdit.setMaximumWidth(85)

        self.detectorRow.addWidget(self.refractoryEdit)

        self.groupingEditLabel = QLabel(self.detectionControls)
        self.groupingEditLabel.setObjectName(u"groupingEditLabel")

        self.detectorRow.addWidget(self.groupingEditLabel)

        self.groupingEdit = QLineEdit(self.detectionControls)
        self.groupingEdit.setObjectName(u"groupingEdit")
        self.groupingEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.groupingEdit.setText(u"0.4")
        self.groupingEdit.setMaximumWidth(85)

        self.detectorRow.addWidget(self.groupingEdit)

        self.detectorRowSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.detectorRow.addItem(self.detectorRowSpacer)


        self.detectionControlsLayout.addLayout(self.detectorRow)

        self.detectionContactsRow = QHBoxLayout()
        self.detectionContactsRow.setObjectName(u"detectionContactsRow")
        self.detectionContactsLabel = QLabel(self.detectionControls)
        self.detectionContactsLabel.setObjectName(u"detectionContactsLabel")

        self.detectionContactsRow.addWidget(self.detectionContactsLabel)

        self.detector1 = QCheckBox(self.detectionControls)
        self.detector1.setObjectName(u"detector1")
        self.detector1.setChecked(True)

        self.detectionContactsRow.addWidget(self.detector1)

        self.detector2 = QCheckBox(self.detectionControls)
        self.detector2.setObjectName(u"detector2")
        self.detector2.setChecked(True)

        self.detectionContactsRow.addWidget(self.detector2)

        self.detector3 = QCheckBox(self.detectionControls)
        self.detector3.setObjectName(u"detector3")
        self.detector3.setChecked(True)

        self.detectionContactsRow.addWidget(self.detector3)

        self.detector4 = QCheckBox(self.detectionControls)
        self.detector4.setObjectName(u"detector4")
        self.detector4.setChecked(True)

        self.detectionContactsRow.addWidget(self.detector4)

        self.detectionContactsRowSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.detectionContactsRow.addItem(self.detectionContactsRowSpacer)


        self.detectionControlsLayout.addLayout(self.detectionContactsRow)

        self.detectionGuide = QLabel(self.detectionControls)
        self.detectionGuide.setObjectName(u"detectionGuide")
        self.detectionGuide.setWordWrap(True)

        self.detectionControlsLayout.addWidget(self.detectionGuide)


        self.detectionTabLayout.addWidget(self.detectionControls)

        self.pageStack.addWidget(self.detectionTab)
        self.comparisonTab = QWidget()
        self.comparisonTab.setObjectName(u"comparisonTab")
        self.comparisonTabLayout = QVBoxLayout(self.comparisonTab)
        self.comparisonTabLayout.setSpacing(6)
        self.comparisonTabLayout.setObjectName(u"comparisonTabLayout")
        self.comparisonTabLayout.setContentsMargins(8, 8, 8, 8)
        self.waveformControls = QFrame(self.comparisonTab)
        self.waveformControls.setObjectName(u"waveformControls")
        self.waveformControls.setProperty(u"analysisPanel", True)
        self.waveformControlsLayout = QVBoxLayout(self.waveformControls)
        self.waveformControlsLayout.setSpacing(5)
        self.waveformControlsLayout.setObjectName(u"waveformControlsLayout")
        self.waveformControlsLayout.setContentsMargins(8, 8, 8, 8)
        self.waveWindowRow = QHBoxLayout()
        self.waveWindowRow.setObjectName(u"waveWindowRow")
        self.preEditLabel = QLabel(self.waveformControls)
        self.preEditLabel.setObjectName(u"preEditLabel")

        self.waveWindowRow.addWidget(self.preEditLabel)

        self.preEdit = QLineEdit(self.waveformControls)
        self.preEdit.setObjectName(u"preEdit")
        self.preEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preEdit.setText(u"1")
        self.preEdit.setMaximumWidth(85)

        self.waveWindowRow.addWidget(self.preEdit)

        self.postEditLabel = QLabel(self.waveformControls)
        self.postEditLabel.setObjectName(u"postEditLabel")

        self.waveWindowRow.addWidget(self.postEditLabel)

        self.postEdit = QLineEdit(self.waveformControls)
        self.postEdit.setObjectName(u"postEdit")
        self.postEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.postEdit.setText(u"2")
        self.postEdit.setMaximumWidth(85)

        self.waveWindowRow.addWidget(self.postEdit)

        self.snippetEditLabel = QLabel(self.waveformControls)
        self.snippetEditLabel.setObjectName(u"snippetEditLabel")

        self.waveWindowRow.addWidget(self.snippetEditLabel)

        self.snippetEdit = QLineEdit(self.waveformControls)
        self.snippetEdit.setObjectName(u"snippetEdit")
        self.snippetEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.snippetEdit.setText(u"16")
        self.snippetEdit.setMaximumWidth(85)

        self.waveWindowRow.addWidget(self.snippetEdit)

        self.waveWindowRowSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.waveWindowRow.addItem(self.waveWindowRowSpacer)


        self.waveformControlsLayout.addLayout(self.waveWindowRow)

        self.waveSelectionRow = QHBoxLayout()
        self.waveSelectionRow.setObjectName(u"waveSelectionRow")
        self.firstGroupEditLabel = QLabel(self.waveformControls)
        self.firstGroupEditLabel.setObjectName(u"firstGroupEditLabel")

        self.waveSelectionRow.addWidget(self.firstGroupEditLabel)

        self.firstGroupEdit = QLineEdit(self.waveformControls)
        self.firstGroupEdit.setObjectName(u"firstGroupEdit")
        self.firstGroupEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.firstGroupEdit.setText(u"1")
        self.firstGroupEdit.setMaximumWidth(85)

        self.waveSelectionRow.addWidget(self.firstGroupEdit)

        self.groupCountEditLabel = QLabel(self.waveformControls)
        self.groupCountEditLabel.setObjectName(u"groupCountEditLabel")

        self.waveSelectionRow.addWidget(self.groupCountEditLabel)

        self.groupCountEdit = QLineEdit(self.waveformControls)
        self.groupCountEdit.setObjectName(u"groupCountEdit")
        self.groupCountEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.groupCountEdit.setText(u"")
        self.groupCountEdit.setMaximumWidth(85)

        self.waveSelectionRow.addWidget(self.groupCountEdit)

        self.rerunButton = QPushButton(self.waveformControls)
        self.rerunButton.setObjectName(u"rerunButton")

        self.waveSelectionRow.addWidget(self.rerunButton)

        self.waveSelectionRowSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.waveSelectionRow.addItem(self.waveSelectionRowSpacer)


        self.waveformControlsLayout.addLayout(self.waveSelectionRow)

        self.waveformGuide = QLabel(self.waveformControls)
        self.waveformGuide.setObjectName(u"waveformGuide")
        self.waveformGuide.setWordWrap(True)

        self.waveformControlsLayout.addWidget(self.waveformGuide)

        self.comparisonStatus = QLabel(self.waveformControls)
        self.comparisonStatus.setObjectName(u"comparisonStatus")
        self.comparisonStatus.setWordWrap(True)
        self.comparisonStatus.setTextFormat(Qt.TextFormat.PlainText)

        self.waveformControlsLayout.addWidget(self.comparisonStatus)


        self.comparisonTabLayout.addWidget(self.waveformControls)

        self.waveformPlotHost = QFrame(self.comparisonTab)
        self.waveformPlotHost.setObjectName(u"waveformPlotHost")
        self.waveformPlotHost.setProperty(u"analysisPanel", True)
        self.waveformPlotLayout = QVBoxLayout(self.waveformPlotHost)
        self.waveformPlotLayout.setObjectName(u"waveformPlotLayout")
        self.waveformPlotLayout.setContentsMargins(3, 3, 3, 3)

        self.comparisonTabLayout.addWidget(self.waveformPlotHost)

        self.comparisonTabLayout.setStretch(1, 1)
        self.pageStack.addWidget(self.comparisonTab)
        self.agreementTab = QWidget()
        self.agreementTab.setObjectName(u"agreementTab")
        self.agreementTabLayout = QVBoxLayout(self.agreementTab)
        self.agreementTabLayout.setSpacing(6)
        self.agreementTabLayout.setObjectName(u"agreementTabLayout")
        self.agreementTabLayout.setContentsMargins(8, 8, 8, 8)
        self.comparisonControls = QFrame(self.agreementTab)
        self.comparisonControls.setObjectName(u"comparisonControls")
        self.comparisonControls.setProperty(u"analysisPanel", True)
        self.comparisonControlsLayout = QVBoxLayout(self.comparisonControls)
        self.comparisonControlsLayout.setSpacing(5)
        self.comparisonControlsLayout.setObjectName(u"comparisonControlsLayout")
        self.comparisonControlsLayout.setContentsMargins(8, 8, 8, 8)
        self.sourceComparisonRow = QHBoxLayout()
        self.sourceComparisonRow.setObjectName(u"sourceComparisonRow")
        self.sourceLabel = QLabel(self.comparisonControls)
        self.sourceLabel.setObjectName(u"sourceLabel")

        self.sourceComparisonRow.addWidget(self.sourceLabel)

        self.sourceCombo = QComboBox(self.comparisonControls)
        self.sourceCombo.setObjectName(u"sourceCombo")

        self.sourceComparisonRow.addWidget(self.sourceCombo)

        self.sourceEvidenceSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.sourceComparisonRow.addItem(self.sourceEvidenceSpacer)


        self.comparisonControlsLayout.addLayout(self.sourceComparisonRow)

        self.matchingSettingsRow = QHBoxLayout()
        self.matchingSettingsRow.setObjectName(u"matchingSettingsRow")
        self.toleranceEditLabel = QLabel(self.comparisonControls)
        self.toleranceEditLabel.setObjectName(u"toleranceEditLabel")

        self.matchingSettingsRow.addWidget(self.toleranceEditLabel)

        self.toleranceEdit = QLineEdit(self.comparisonControls)
        self.toleranceEdit.setObjectName(u"toleranceEdit")
        self.toleranceEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toleranceEdit.setText(u"2")
        self.toleranceEdit.setMaximumWidth(85)

        self.matchingSettingsRow.addWidget(self.toleranceEdit)

        self.matchButton = QPushButton(self.comparisonControls)
        self.matchButton.setObjectName(u"matchButton")

        self.matchingSettingsRow.addWidget(self.matchButton)

        self.analysisExportButton = QPushButton(self.comparisonControls)
        self.analysisExportButton.setObjectName(u"analysisExportButton")

        self.matchingSettingsRow.addWidget(self.analysisExportButton)

        self.sourceComparisonRowSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.matchingSettingsRow.addItem(self.sourceComparisonRowSpacer)


        self.comparisonControlsLayout.addLayout(self.matchingSettingsRow)

        self.baselineRow = QHBoxLayout()
        self.baselineRow.setObjectName(u"baselineRow")
        self.baselineStartLabel = QLabel(self.comparisonControls)
        self.baselineStartLabel.setObjectName(u"baselineStartLabel")

        self.baselineRow.addWidget(self.baselineStartLabel)

        self.baselineStartEdit = QLineEdit(self.comparisonControls)
        self.baselineStartEdit.setObjectName(u"baselineStartEdit")
        self.baselineStartEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.baselineStartEdit.setMaximumWidth(85)

        self.baselineRow.addWidget(self.baselineStartEdit)

        self.baselineCountLabel = QLabel(self.comparisonControls)
        self.baselineCountLabel.setObjectName(u"baselineCountLabel")

        self.baselineRow.addWidget(self.baselineCountLabel)

        self.baselineCountEdit = QLineEdit(self.comparisonControls)
        self.baselineCountEdit.setObjectName(u"baselineCountEdit")
        self.baselineCountEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.baselineCountEdit.setMaximumWidth(85)

        self.baselineRow.addWidget(self.baselineCountEdit)

        self.baselineRowSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.baselineRow.addItem(self.baselineRowSpacer)


        self.comparisonControlsLayout.addLayout(self.baselineRow)


        self.agreementTabLayout.addWidget(self.comparisonControls)

        self.evidenceGuide = QLabel(self.agreementTab)
        self.evidenceGuide.setObjectName(u"evidenceGuide")
        self.evidenceGuide.setWordWrap(True)

        self.agreementTabLayout.addWidget(self.evidenceGuide)

        self.comparisonGuide = QLabel(self.agreementTab)
        self.comparisonGuide.setObjectName(u"comparisonGuide")
        self.comparisonGuide.setWordWrap(True)

        self.agreementTabLayout.addWidget(self.comparisonGuide)

        self.measurementStatus = QLabel(self.agreementTab)
        self.measurementStatus.setObjectName(u"measurementStatus")
        self.measurementStatus.setWordWrap(True)

        self.agreementTabLayout.addWidget(self.measurementStatus)

        self.measurementTable = QTableWidget(self.agreementTab)
        if (self.measurementTable.columnCount() < 5):
            self.measurementTable.setColumnCount(5)
        __qtablewidgetitem = QTableWidgetItem()
        self.measurementTable.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.measurementTable.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.measurementTable.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.measurementTable.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.measurementTable.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        self.measurementTable.setObjectName(u"measurementTable")
        self.measurementTable.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.measurementTable.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.measurementTable.setMinimumHeight(106)
        self.measurementTable.setMaximumHeight(116)

        self.agreementTabLayout.addWidget(self.measurementTable)

        self.comparisonDetails = QPlainTextEdit(self.agreementTab)
        self.comparisonDetails.setObjectName(u"comparisonDetails")
        self.comparisonDetails.setReadOnly(True)

        self.agreementTabLayout.addWidget(self.comparisonDetails)

        self.agreementTabLayout.setStretch(5, 1)
        self.pageStack.addWidget(self.agreementTab)
        self.spectrumTab = QWidget()
        self.spectrumTab.setObjectName(u"spectrumTab")
        self.spectrumLayout = QVBoxLayout(self.spectrumTab)
        self.spectrumLayout.setObjectName(u"spectrumLayout")
        self.spectrumControls = QFrame(self.spectrumTab)
        self.spectrumControls.setObjectName(u"spectrumControls")
        self.spectrumControls.setProperty(u"analysisPanel", True)
        self.spectrumControlsLayout = QVBoxLayout(self.spectrumControls)
        self.spectrumControlsLayout.setSpacing(5)
        self.spectrumControlsLayout.setObjectName(u"spectrumControlsLayout")
        self.spectrumControlsLayout.setContentsMargins(8, 8, 8, 8)
        self.spectrumToolbar = QHBoxLayout()
        self.spectrumToolbar.setObjectName(u"spectrumToolbar")
        self.spectrumContactLabel = QLabel(self.spectrumControls)
        self.spectrumContactLabel.setObjectName(u"spectrumContactLabel")

        self.spectrumToolbar.addWidget(self.spectrumContactLabel)

        self.spectrumContact = QComboBox(self.spectrumControls)
        self.spectrumContact.addItem("")
        self.spectrumContact.addItem("")
        self.spectrumContact.addItem("")
        self.spectrumContact.addItem("")
        self.spectrumContact.setObjectName(u"spectrumContact")

        self.spectrumToolbar.addWidget(self.spectrumContact)

        self.spectrumStatus = QLabel(self.spectrumControls)
        self.spectrumStatus.setObjectName(u"spectrumStatus")
        self.spectrumStatus.setWordWrap(True)

        self.spectrumToolbar.addWidget(self.spectrumStatus)


        self.spectrumControlsLayout.addLayout(self.spectrumToolbar)

        self.spectrumGuide = QLabel(self.spectrumControls)
        self.spectrumGuide.setObjectName(u"spectrumGuide")
        self.spectrumGuide.setWordWrap(True)

        self.spectrumControlsLayout.addWidget(self.spectrumGuide)


        self.spectrumLayout.addWidget(self.spectrumControls)

        self.spectrumHost = QFrame(self.spectrumTab)
        self.spectrumHost.setObjectName(u"spectrumHost")
        self.spectrumHost.setProperty(u"analysisPanel", True)
        self.spectrumPlotLayout = QVBoxLayout(self.spectrumHost)
        self.spectrumPlotLayout.setObjectName(u"spectrumPlotLayout")
        self.spectrumPlotLayout.setContentsMargins(3, 3, 3, 3)

        self.spectrumLayout.addWidget(self.spectrumHost)

        self.spectrumLayout.setStretch(1, 1)
        self.pageStack.addWidget(self.spectrumTab)

        self.rootLayout.addWidget(self.pageStack)

        self.analysisFooter = QFrame(ExtracellularRecording)
        self.analysisFooter.setObjectName(u"analysisFooter")
        self.analysisFooter.setProperty(u"analysisPanel", True)
        self.analysisFooterLayout = QVBoxLayout(self.analysisFooter)
        self.analysisFooterLayout.setSpacing(5)
        self.analysisFooterLayout.setObjectName(u"analysisFooterLayout")
        self.analysisFooterLayout.setContentsMargins(8, 8, 8, 8)
        self.analysisActions = QHBoxLayout()
        self.analysisActions.setObjectName(u"analysisActions")
        self.runButton = QPushButton(self.analysisFooter)
        self.runButton.setObjectName(u"runButton")
        self.runButton.setFont(font2)

        self.analysisActions.addWidget(self.runButton)

        self.pinButton = QPushButton(self.analysisFooter)
        self.pinButton.setObjectName(u"pinButton")
        self.pinButton.setFont(font2)

        self.analysisActions.addWidget(self.pinButton)


        self.analysisFooterLayout.addLayout(self.analysisActions)

        self.analysisStatus = QLabel(self.analysisFooter)
        self.analysisStatus.setObjectName(u"analysisStatus")
        self.analysisStatus.setProperty(u"analysisStatus", True)
        self.analysisStatus.setWordWrap(True)
        self.analysisStatus.setTextFormat(Qt.TextFormat.PlainText)

        self.analysisFooterLayout.addWidget(self.analysisStatus)

        self.analysisSelection = QLabel(self.analysisFooter)
        self.analysisSelection.setObjectName(u"analysisSelection")
        self.analysisSelection.setProperty(u"analysisStatus", True)
        self.analysisSelection.setWordWrap(True)
        self.analysisSelection.setTextFormat(Qt.TextFormat.PlainText)

        self.analysisFooterLayout.addWidget(self.analysisSelection)


        self.rootLayout.addWidget(self.analysisFooter)

        self.rootLayout.setStretch(2, 1)
#if QT_CONFIG(shortcut)
        self.stageLabel.setBuddy(self.stageCombo)
        self.indexLabel.setBuddy(self.indexEdit)
        self.countLabel.setBuddy(self.countEdit)
        self.referenceLabel.setBuddy(self.referenceCombo)
        self.lowEditLabel.setBuddy(self.lowEdit)
        self.highEditLabel.setBuddy(self.highEdit)
        self.notchLabel.setBuddy(self.notchCombo)
        self.polarityLabel.setBuddy(self.polarityCombo)
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
        self.baselineStartLabel.setBuddy(self.baselineStartEdit)
        self.baselineCountLabel.setBuddy(self.baselineCountEdit)
        self.spectrumContactLabel.setBuddy(self.spectrumContact)
#endif // QT_CONFIG(shortcut)

        self.retranslateUi(ExtracellularRecording)

        self.pageStack.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ExtracellularRecording)
    # setupUi

    def retranslateUi(self, ExtracellularRecording):
        self.analysisHeading.setText(QCoreApplication.translate("ExtracellularRecording", u"Extracellular Data Analysis", None))
        self.navRecording.setText(QCoreApplication.translate("ExtracellularRecording", u"Recording", None))
        self.navProcessing.setText(QCoreApplication.translate("ExtracellularRecording", u"Processing", None))
        self.navDetection.setText(QCoreApplication.translate("ExtracellularRecording", u"Detection", None))
        self.navWaveforms.setText(QCoreApplication.translate("ExtracellularRecording", u"Waveforms", None))
        self.navComparison.setText(QCoreApplication.translate("ExtracellularRecording", u"Comparison", None))
        self.navSpectrum.setText(QCoreApplication.translate("ExtracellularRecording", u"Spectrum", None))
        self.openButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Load extracellular recording\u2026", None))
#if QT_CONFIG(tooltip)
        self.metadataButton.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"View the acquisition settings and source evidence for the loaded recording.", None))
#endif // QT_CONFIG(tooltip)
        self.metadataButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Metadata\u2026", None))
        self.statusLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Open a session manifest or an extracellular CSV.", None))
        self.stageLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"View saved signal", None))
#if QT_CONFIG(tooltip)
        self.stageCombo.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"Broadband is before reference/filtering. Live processed is the saved output of the original Scope settings. Offline analysis always starts from broadband.", None))
#endif // QT_CONFIG(tooltip)
        self.indexLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Start sample index", None))
#if QT_CONFIG(tooltip)
        self.indexEdit.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"Accepted recording index, which may start above zero. Changing the interval clears A and B.", None))
#endif // QT_CONFIG(tooltip)
        self.countLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Samples requested", None))
        self.previewButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Preview", None))
        self.exportButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Export CSV\u2026", None))
        self.recordingGuide.setText(QCoreApplication.translate("ExtracellularRecording", u"Choose a saved signal and sample interval to preview.", None))
        self.metadataBackButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Back to Recording", None))
        self.metadata.setPlaceholderText(QCoreApplication.translate("ExtracellularRecording", u"Open a recording to see its acquisition summary.", None))
        self.referenceLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Reference", None))
        self.referenceCombo.setItemText(0, QCoreApplication.translate("ExtracellularRecording", u"None", None))
        self.referenceCombo.setItemText(1, QCoreApplication.translate("ExtracellularRecording", u"Common average (CAR)", None))
        self.referenceCombo.setItemText(2, QCoreApplication.translate("ExtracellularRecording", u"Single contact", None))

#if QT_CONFIG(tooltip)
        self.referenceCombo.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"Subtract one contact or the mean of the selected contacts from all four recorded signals.", None))
#endif // QT_CONFIG(tooltip)
        self.refContactsLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Contacts in average", None))
        self.reference1.setText(QCoreApplication.translate("ExtracellularRecording", u"E1", None))
        self.reference2.setText(QCoreApplication.translate("ExtracellularRecording", u"E2", None))
        self.reference3.setText(QCoreApplication.translate("ExtracellularRecording", u"E3", None))
        self.reference4.setText(QCoreApplication.translate("ExtracellularRecording", u"E4", None))
        self.singleReferenceCombo.setItemText(0, QCoreApplication.translate("ExtracellularRecording", u"E1", None))
        self.singleReferenceCombo.setItemText(1, QCoreApplication.translate("ExtracellularRecording", u"E2", None))
        self.singleReferenceCombo.setItemText(2, QCoreApplication.translate("ExtracellularRecording", u"E3", None))
        self.singleReferenceCombo.setItemText(3, QCoreApplication.translate("ExtracellularRecording", u"E4", None))

#if QT_CONFIG(tooltip)
        self.singleReferenceCombo.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"Subtract this contact from all four signals. Its own output becomes zero.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.bandpassCheck.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"Filter a fresh copy of the saved broadband. Warm-up rows after each reset are excluded from detection.", None))
#endif // QT_CONFIG(tooltip)
        self.bandpassCheck.setText(QCoreApplication.translate("ExtracellularRecording", u"Causal bandpass", None))
        self.lowEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Low (Hz)", None))
        self.highEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"High (Hz)", None))
        self.notchLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Mains notch", None))
        self.notchCombo.setItemText(0, QCoreApplication.translate("ExtracellularRecording", u"Off", None))
        self.notchCombo.setItemText(1, QCoreApplication.translate("ExtracellularRecording", u"50 Hz", None))
        self.notchCombo.setItemText(2, QCoreApplication.translate("ExtracellularRecording", u"60 Hz", None))

#if QT_CONFIG(tooltip)
        self.notchCombo.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"Causal notch, Q = 30. Turn off bandpass to isolate the notch effect.", None))
#endif // QT_CONFIG(tooltip)
        self.processingGuide.setText(QCoreApplication.translate("ExtracellularRecording", u"Choose how to transform the saved broadband, then run B. CAR subtracts the selected contacts\u2019 mean from all four contacts. It removes shared neuronal signal as well as shared noise; identical contacts become zero.", None))
        self.polarityLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Polarity", None))
        self.polarityCombo.setItemText(0, QCoreApplication.translate("ExtracellularRecording", u"Negative", None))
        self.polarityCombo.setItemText(1, QCoreApplication.translate("ExtracellularRecording", u"Positive", None))
        self.polarityCombo.setItemText(2, QCoreApplication.translate("ExtracellularRecording", u"Both", None))

#if QT_CONFIG(tooltip)
        self.polarityCombo.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"Both applies symmetric positive and negative thresholds with one refractory timer per contact.", None))
#endif // QT_CONFIG(tooltip)
        self.thresholdEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Negative threshold (\u00b5V)", None))
#if QT_CONFIG(tooltip)
        self.thresholdEdit.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"Use a negative value for Negative, a positive value for Positive, and a positive magnitude for Both.", None))
#endif // QT_CONFIG(tooltip)
        self.refractoryEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Refractory (ms)", None))
#if QT_CONFIG(tooltip)
        self.refractoryEdit.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"Minimum time between accepted crossings on one contact. A filter can create multiple crossings from one source waveform.", None))
#endif // QT_CONFIG(tooltip)
        self.groupingEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Grouping (ms)", None))
#if QT_CONFIG(tooltip)
        self.groupingEdit.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"The grouping window starts at the first accepted crossing. A crossing at exact expiry starts a new group.", None))
#endif // QT_CONFIG(tooltip)
        self.detectionContactsLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Detection contacts", None))
        self.detector1.setText(QCoreApplication.translate("ExtracellularRecording", u"E1", None))
        self.detector2.setText(QCoreApplication.translate("ExtracellularRecording", u"E2", None))
        self.detector3.setText(QCoreApplication.translate("ExtracellularRecording", u"E3", None))
        self.detector4.setText(QCoreApplication.translate("ExtracellularRecording", u"E4", None))
        self.detectionGuide.setText(QCoreApplication.translate("ExtracellularRecording", u"A threshold crossing is not proof of a spike. Refractory and grouping windows affect whether two waveform lobes form one event or two.", None))
        self.preEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Pre-event (ms)", None))
#if QT_CONFIG(tooltip)
        self.preEdit.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"Duration before the grouped detection anchor. Windows crossing an interval, segment, epoch or warm-up boundary are excluded.", None))
#endif // QT_CONFIG(tooltip)
        self.postEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Post-event (ms)", None))
        self.snippetEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Individual overlays", None))
#if QT_CONFIG(tooltip)
        self.snippetEdit.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"Display up to this many individual windows. The mean still uses all valid selected groups.", None))
#endif // QT_CONFIG(tooltip)
        self.firstGroupEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"First group", None))
        self.groupCountEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Group count", None))
        self.groupCountEdit.setPlaceholderText(QCoreApplication.translate("ExtracellularRecording", u"All remaining", None))
        self.rerunButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Update B waveforms", None))
        self.waveformGuide.setText(QCoreApplication.translate("ExtracellularRecording", u"Inspect short windows around grouped detections. Zero marks the first crossing in a group. The mean includes every valid selected window; overlays show a limited sample. These waveforms have not been sorted into neurons.", None))
        self.sourceLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Source evidence", None))
        self.toleranceEditLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Match tolerance (ms)", None))
#if QT_CONFIG(tooltip)
        self.toleranceEdit.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"Maximum timing difference for one-to-one matching. Larger tolerance can associate unrelated nearby events.", None))
#endif // QT_CONFIG(tooltip)
        self.matchButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Refresh agreement", None))
        self.analysisExportButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Export analysis\u2026", None))
        self.baselineStartLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Quiet interval start index", None))
#if QT_CONFIG(tooltip)
        self.baselineStartEdit.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"Absolute accepted sample index within the analysed interval. Choose a quiet portion of the trace.", None))
#endif // QT_CONFIG(tooltip)
        self.baselineCountLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Samples", None))
#if QT_CONFIG(tooltip)
        self.baselineCountEdit.setToolTip(QCoreApplication.translate("ExtracellularRecording", u"Choose at least two samples in one settled, contiguous block.", None))
#endif // QT_CONFIG(tooltip)
        self.evidenceGuide.setText(QCoreApplication.translate("ExtracellularRecording", u"Source evidence is optional. Inferred Vm launches are proxies; native emulator events are separate evidence when saved. An unmatched detection can reflect noise, filter lobes, timing or overlapping sources.", None))
        self.comparisonGuide.setText(QCoreApplication.translate("ExtracellularRecording", u"A and B are analyses of the same recording. Run B and save it as baseline A, then change one setting and rerun B. Dashed traces show A; solid traces show B. Matching counts describe temporal agreement, not spike identity.", None))
        self.measurementStatus.setText("")
        ___qtablewidgetitem = self.measurementTable.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("ExtracellularRecording", u"Contact", None));
        ___qtablewidgetitem1 = self.measurementTable.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("ExtracellularRecording", u"A RMS (\u00b5V)", None));
        ___qtablewidgetitem2 = self.measurementTable.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("ExtracellularRecording", u"B RMS (\u00b5V)", None));
        ___qtablewidgetitem3 = self.measurementTable.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("ExtracellularRecording", u"A mean p-p (\u00b5V)", None));
        ___qtablewidgetitem4 = self.measurementTable.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("ExtracellularRecording", u"B mean p-p (\u00b5V)", None));
        self.spectrumContactLabel.setText(QCoreApplication.translate("ExtracellularRecording", u"Contact", None))
        self.spectrumContact.setItemText(0, QCoreApplication.translate("ExtracellularRecording", u"E1", None))
        self.spectrumContact.setItemText(1, QCoreApplication.translate("ExtracellularRecording", u"E2", None))
        self.spectrumContact.setItemText(2, QCoreApplication.translate("ExtracellularRecording", u"E3", None))
        self.spectrumContact.setItemText(3, QCoreApplication.translate("ExtracellularRecording", u"E4", None))

        self.spectrumStatus.setText("")
        self.spectrumGuide.setText(QCoreApplication.translate("ExtracellularRecording", u"Compare the same settled samples. Dashed A, solid B. Turn bandpass off to examine mains pickup.", None))
        self.runButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Run B \u00b7 apply current settings", None))
        self.pinButton.setText(QCoreApplication.translate("ExtracellularRecording", u"Save completed B as baseline A", None))
        pass
    # retranslateUi
