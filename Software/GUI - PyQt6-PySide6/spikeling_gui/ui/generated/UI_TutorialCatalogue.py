# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'UI_TutorialCatalogue.ui'
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
from PySide6.QtWidgets import (QApplication, QButtonGroup, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QTextBrowser,
    QVBoxLayout, QWidget)

class Ui_TutorialCatalogue(object):
    def setupUi(self, TutorialCatalogue):
        if not TutorialCatalogue.objectName():
            TutorialCatalogue.setObjectName(u"TutorialCatalogue")
        TutorialCatalogue.resize(910, 620)
        TutorialCatalogue.setMinimumSize(QSize(690, 440))
        TutorialCatalogue.setStyleSheet(u"QPushButton {\n"
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
"QLineEdit, QListWidget, QTextBrowser {\n"
"    background: #073642;\n"
"    color: #BECDCD;\n"
"    border: 1px solid #586E75;\n"
"    border-radius: 5px;\n"
"    padding: 4px 7px;\n"
"}\n"
"QLineEdit:focus, QListWidget:focus, QTextBrowser:focus {\n"
"    border: 2px solid #268BD2;\n"
"}\n"
"QPushButton[tutorialTab=\"true\"] {\n"
"    color: #BECDCD;\n"
"    background: transparent;\n"
"    border: 0;\n"
"    border-bottom: 2px solid transparent;\n"
"    padding: 5px 10px;\n"
"}\n"
"QPushButton[tutorialTab=\"true\"]:checked {\n"
"    color: #268BD2;\n"
"    border-bottom: 2px solid #268BD2;\n"
"}\n"
"QPushButton[tutorialTab=\"true\"]:hov"
                        "er, QPushButton[tutorialTab=\"true\"]:focus {\n"
"    background: #073642;\n"
"}\n"
"QFrame[tutorialPanel=\"true\"] {\n"
"    background: #002B36;\n"
"    border: 1px solid #073642;\n"
"    border-radius: 8px;\n"
"}\n"
"QListWidget {\n"
"    outline: 0;\n"
"}\n"
"QListWidget::item {\n"
"    padding: 5px;\n"
"}\n"
"QListWidget::item:selected {\n"
"    color: #BECDCD;\n"
"    background: #002B36;\n"
"    border-left: 2px solid #268BD2;\n"
"}\n"
"")
        self.rootLayout = QVBoxLayout(TutorialCatalogue)
        self.rootLayout.setSpacing(6)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(5, 5, 5, 5)
        self.titleLabel = QLabel(TutorialCatalogue)
        self.titleLabel.setObjectName(u"titleLabel")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.titleLabel.setFont(font)

        self.rootLayout.addWidget(self.titleLabel)

        self.categoryLayout = QHBoxLayout()
        self.categoryLayout.setSpacing(6)
        self.categoryLayout.setObjectName(u"categoryLayout")
        self.categoryLayout.setContentsMargins(0, 0, 0, 0)
        self.allTutorialsTab = QPushButton(TutorialCatalogue)
        self.categoryButtons = QButtonGroup(TutorialCatalogue)
        self.categoryButtons.setObjectName(u"categoryButtons")
        self.categoryButtons.addButton(self.allTutorialsTab)
        self.allTutorialsTab.setObjectName(u"allTutorialsTab")
        font1 = QFont()
        font1.setPointSize(12)
        font1.setBold(True)
        self.allTutorialsTab.setFont(font1)
        self.allTutorialsTab.setMinimumHeight(34)
        self.allTutorialsTab.setCheckable(True)
        self.allTutorialsTab.setChecked(True)
        self.allTutorialsTab.setProperty(u"tutorialTab", True)

        self.categoryLayout.addWidget(self.allTutorialsTab)

        self.neuronInterfaceTab = QPushButton(TutorialCatalogue)
        self.categoryButtons.addButton(self.neuronInterfaceTab)
        self.neuronInterfaceTab.setObjectName(u"neuronInterfaceTab")
        self.neuronInterfaceTab.setFont(font1)
        self.neuronInterfaceTab.setMinimumHeight(34)
        self.neuronInterfaceTab.setCheckable(True)
        self.neuronInterfaceTab.setProperty(u"tutorialModule", u"Neuron Interface")
        self.neuronInterfaceTab.setProperty(u"tutorialTab", True)

        self.categoryLayout.addWidget(self.neuronInterfaceTab)

        self.neuronEmulatorTab = QPushButton(TutorialCatalogue)
        self.categoryButtons.addButton(self.neuronEmulatorTab)
        self.neuronEmulatorTab.setObjectName(u"neuronEmulatorTab")
        self.neuronEmulatorTab.setFont(font1)
        self.neuronEmulatorTab.setMinimumHeight(34)
        self.neuronEmulatorTab.setCheckable(True)
        self.neuronEmulatorTab.setProperty(u"tutorialModule", u"Neuron Emulator")
        self.neuronEmulatorTab.setProperty(u"tutorialTab", True)

        self.categoryLayout.addWidget(self.neuronEmulatorTab)

        self.neuronAnalysisTab = QPushButton(TutorialCatalogue)
        self.categoryButtons.addButton(self.neuronAnalysisTab)
        self.neuronAnalysisTab.setObjectName(u"neuronAnalysisTab")
        self.neuronAnalysisTab.setFont(font1)
        self.neuronAnalysisTab.setMinimumHeight(34)
        self.neuronAnalysisTab.setCheckable(True)
        self.neuronAnalysisTab.setProperty(u"tutorialModule", u"Neuron Data Analysis")
        self.neuronAnalysisTab.setProperty(u"tutorialTab", True)

        self.categoryLayout.addWidget(self.neuronAnalysisTab)

        self.categorySpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.categoryLayout.addItem(self.categorySpacer)


        self.rootLayout.addLayout(self.categoryLayout)

        self.bodyLayout = QHBoxLayout()
        self.bodyLayout.setSpacing(6)
        self.bodyLayout.setObjectName(u"bodyLayout")
        self.tutorialListFrame = QFrame(TutorialCatalogue)
        self.tutorialListFrame.setObjectName(u"tutorialListFrame")
        self.tutorialListFrame.setProperty(u"tutorialPanel", True)
        self.leftLayout = QVBoxLayout(self.tutorialListFrame)
        self.leftLayout.setSpacing(6)
        self.leftLayout.setObjectName(u"leftLayout")
        self.leftLayout.setContentsMargins(8, 8, 8, 8)
        self.searchEdit = QLineEdit(self.tutorialListFrame)
        self.searchEdit.setObjectName(u"searchEdit")
        self.searchEdit.setClearButtonEnabled(True)

        self.leftLayout.addWidget(self.searchEdit)

        self.tutorialList = QListWidget(self.tutorialListFrame)
        self.tutorialList.setObjectName(u"tutorialList")
        self.tutorialList.setWordWrap(True)

        self.leftLayout.addWidget(self.tutorialList)


        self.bodyLayout.addWidget(self.tutorialListFrame)

        self.detailsFrame = QFrame(TutorialCatalogue)
        self.detailsFrame.setObjectName(u"detailsFrame")
        self.detailsFrame.setProperty(u"tutorialPanel", True)
        self.detailsLayout = QVBoxLayout(self.detailsFrame)
        self.detailsLayout.setSpacing(6)
        self.detailsLayout.setObjectName(u"detailsLayout")
        self.detailsLayout.setContentsMargins(8, 8, 8, 8)
        self.nameLabel = QLabel(self.detailsFrame)
        self.nameLabel.setObjectName(u"nameLabel")
        self.nameLabel.setWordWrap(True)
        self.nameLabel.setFont(font1)

        self.detailsLayout.addWidget(self.nameLabel)

        self.metaLabel = QLabel(self.detailsFrame)
        self.metaLabel.setObjectName(u"metaLabel")
        self.metaLabel.setWordWrap(True)

        self.detailsLayout.addWidget(self.metaLabel)

        self.descriptionText = QTextBrowser(self.detailsFrame)
        self.descriptionText.setObjectName(u"descriptionText")
        self.descriptionText.setOpenExternalLinks(False)

        self.detailsLayout.addWidget(self.descriptionText)

        self.statusLabel = QLabel(self.detailsFrame)
        self.statusLabel.setObjectName(u"statusLabel")
        self.statusLabel.setWordWrap(True)

        self.detailsLayout.addWidget(self.statusLabel)

        self.startButton = QPushButton(self.detailsFrame)
        self.startButton.setObjectName(u"startButton")
        self.startButton.setEnabled(False)

        self.detailsLayout.addWidget(self.startButton, 0, Qt.AlignRight)


        self.bodyLayout.addWidget(self.detailsFrame)

        self.bodyLayout.setStretch(0, 2)
        self.bodyLayout.setStretch(1, 3)

        self.rootLayout.addLayout(self.bodyLayout)

        self.footerLayout = QHBoxLayout()
        self.footerLayout.setObjectName(u"footerLayout")
        self.flexSpacer = QSpacerItem(40, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.footerLayout.addItem(self.flexSpacer)

        self.closeButton = QPushButton(TutorialCatalogue)
        self.closeButton.setObjectName(u"closeButton")

        self.footerLayout.addWidget(self.closeButton)


        self.rootLayout.addLayout(self.footerLayout)

        self.rootLayout.setStretch(2, 1)

        self.retranslateUi(TutorialCatalogue)

        QMetaObject.connectSlotsByName(TutorialCatalogue)
    # setupUi

    def retranslateUi(self, TutorialCatalogue):
        self.titleLabel.setText(QCoreApplication.translate("TutorialCatalogue", u"Spikeling Tutorials", None))
        self.allTutorialsTab.setText(QCoreApplication.translate("TutorialCatalogue", u"All tutorials", None))
        self.neuronInterfaceTab.setText(QCoreApplication.translate("TutorialCatalogue", u"Neuron Interface", None))
        self.neuronEmulatorTab.setText(QCoreApplication.translate("TutorialCatalogue", u"Neuron Emulator", None))
        self.neuronAnalysisTab.setText(QCoreApplication.translate("TutorialCatalogue", u"Neuron Data Analysis", None))
        self.searchEdit.setPlaceholderText(QCoreApplication.translate("TutorialCatalogue", u"Search tutorials", None))
#if QT_CONFIG(accessibility)
        self.searchEdit.setAccessibleName(QCoreApplication.translate("TutorialCatalogue", u"Search tutorials", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(accessibility)
        self.tutorialList.setAccessibleName(QCoreApplication.translate("TutorialCatalogue", u"Available tutorials", None))
#endif // QT_CONFIG(accessibility)
        self.nameLabel.setText(QCoreApplication.translate("TutorialCatalogue", u"Choose a tutorial", None))
        self.startButton.setText(QCoreApplication.translate("TutorialCatalogue", u"Start tutorial", None))
        self.closeButton.setText(QCoreApplication.translate("TutorialCatalogue", u"Return to Spikeling", None))
        pass
    # retranslateUi
