# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'UI_About.ui'
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
from PySide6.QtWidgets import (QApplication, QCommandLinkButton, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPlainTextEdit, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QSplitter, QStackedWidget,
    QTabWidget, QTextBrowser, QVBoxLayout, QWidget)

class Ui_AboutPanel(object):
    def setupUi(self, AboutPanel):
        if not AboutPanel.objectName():
            AboutPanel.setObjectName(u"AboutPanel")
        AboutPanel.resize(1120, 800)
        font = QFont()
        font.setFamilies([u"Segoe UI"])
        font.setPointSize(10)
        AboutPanel.setFont(font)
        self.About_rootLayout = QVBoxLayout(AboutPanel)
        self.About_rootLayout.setSpacing(12)
        self.About_rootLayout.setObjectName(u"About_rootLayout")
        self.About_rootLayout.setContentsMargins(22, 22, 22, 22)
        self.About_titleLabel = QLabel(AboutPanel)
        self.About_titleLabel.setObjectName(u"About_titleLabel")
        self.About_titleLabel.setWordWrap(True)
        font1 = QFont()
        font1.setPointSize(22)
        font1.setBold(True)
        self.About_titleLabel.setFont(font1)

        self.About_rootLayout.addWidget(self.About_titleLabel)

        self.About_subtitleLabel = QLabel(AboutPanel)
        self.About_subtitleLabel.setObjectName(u"About_subtitleLabel")
        self.About_subtitleLabel.setWordWrap(True)
        font2 = QFont()
        font2.setPointSize(10)
        font2.setBold(False)
        self.About_subtitleLabel.setFont(font2)

        self.About_rootLayout.addWidget(self.About_subtitleLabel)

        self.About_navigation = QWidget(AboutPanel)
        self.About_navigation.setObjectName(u"About_navigation")
        self.About_navigationLayout = QHBoxLayout(self.About_navigation)
        self.About_navigationLayout.setSpacing(12)
        self.About_navigationLayout.setObjectName(u"About_navigationLayout")
        self.About_navigationLayout.setContentsMargins(0, 0, 0, 0)
        self.About_navProject = QPushButton(self.About_navigation)
        self.About_navProject.setObjectName(u"About_navProject")
        self.About_navProject.setMinimumHeight(40)
        self.About_navProject.setCheckable(True)
        self.About_navProject.setAutoExclusive(True)
        self.About_navProject.setChecked(True)

        self.About_navigationLayout.addWidget(self.About_navProject)

        self.About_navModels = QPushButton(self.About_navigation)
        self.About_navModels.setObjectName(u"About_navModels")
        self.About_navModels.setMinimumHeight(40)
        self.About_navModels.setCheckable(True)
        self.About_navModels.setAutoExclusive(True)

        self.About_navigationLayout.addWidget(self.About_navModels)

        self.About_navReferences = QPushButton(self.About_navigation)
        self.About_navReferences.setObjectName(u"About_navReferences")
        self.About_navReferences.setMinimumHeight(40)
        self.About_navReferences.setCheckable(True)
        self.About_navReferences.setAutoExclusive(True)

        self.About_navigationLayout.addWidget(self.About_navReferences)

        self.About_navScience = QPushButton(self.About_navigation)
        self.About_navScience.setObjectName(u"About_navScience")
        self.About_navScience.setMinimumHeight(40)
        self.About_navScience.setCheckable(True)
        self.About_navScience.setAutoExclusive(True)

        self.About_navigationLayout.addWidget(self.About_navScience)

        self.About_navSoftware = QPushButton(self.About_navigation)
        self.About_navSoftware.setObjectName(u"About_navSoftware")
        self.About_navSoftware.setMinimumHeight(40)
        self.About_navSoftware.setCheckable(True)
        self.About_navSoftware.setAutoExclusive(True)

        self.About_navigationLayout.addWidget(self.About_navSoftware)


        self.About_rootLayout.addWidget(self.About_navigation)

        self.About_breadcrumbLabel = QLabel(AboutPanel)
        self.About_breadcrumbLabel.setObjectName(u"About_breadcrumbLabel")
        self.About_breadcrumbLabel.setWordWrap(True)
        font3 = QFont()
        font3.setPointSize(9)
        font3.setBold(False)
        self.About_breadcrumbLabel.setFont(font3)

        self.About_rootLayout.addWidget(self.About_breadcrumbLabel)

        self.About_stack = QStackedWidget(AboutPanel)
        self.About_stack.setObjectName(u"About_stack")
        self.About_projectPage = QWidget()
        self.About_projectPage.setObjectName(u"About_projectPage")
        self.About_projectLayout = QVBoxLayout(self.About_projectPage)
        self.About_projectLayout.setSpacing(12)
        self.About_projectLayout.setObjectName(u"About_projectLayout")
        self.About_projectScroll = QScrollArea(self.About_projectPage)
        self.About_projectScroll.setObjectName(u"About_projectScroll")
        self.About_projectScroll.setWidgetResizable(True)
        self.About_projectContents = QWidget()
        self.About_projectContents.setObjectName(u"About_projectContents")
        self.About_projectContentsLayout = QVBoxLayout(self.About_projectContents)
        self.About_projectContentsLayout.setSpacing(12)
        self.About_projectContentsLayout.setObjectName(u"About_projectContentsLayout")
        self.About_heroBox = QGroupBox(self.About_projectContents)
        self.About_heroBox.setObjectName(u"About_heroBox")
        self.About_heroLayout = QVBoxLayout(self.About_heroBox)
        self.About_heroLayout.setSpacing(12)
        self.About_heroLayout.setObjectName(u"About_heroLayout")
        self.About_missionLabel = QLabel(self.About_heroBox)
        self.About_missionLabel.setObjectName(u"About_missionLabel")
        self.About_missionLabel.setWordWrap(True)
        font4 = QFont()
        font4.setPointSize(14)
        font4.setBold(True)
        self.About_missionLabel.setFont(font4)

        self.About_heroLayout.addWidget(self.About_missionLabel)

        self.About_introLabel = QLabel(self.About_heroBox)
        self.About_introLabel.setObjectName(u"About_introLabel")
        self.About_introLabel.setWordWrap(True)
        font5 = QFont()
        font5.setPointSize(11)
        font5.setBold(False)
        self.About_introLabel.setFont(font5)

        self.About_heroLayout.addWidget(self.About_introLabel)


        self.About_projectContentsLayout.addWidget(self.About_heroBox)

        self.About_exploreLabel = QLabel(self.About_projectContents)
        self.About_exploreLabel.setObjectName(u"About_exploreLabel")
        self.About_exploreLabel.setWordWrap(True)
        font6 = QFont()
        font6.setPointSize(15)
        font6.setBold(True)
        self.About_exploreLabel.setFont(font6)

        self.About_projectContentsLayout.addWidget(self.About_exploreLabel)

        self.About_cards = QWidget(self.About_projectContents)
        self.About_cards.setObjectName(u"About_cards")
        self.About_cardsLayout = QGridLayout(self.About_cards)
        self.About_cardsLayout.setSpacing(12)
        self.About_cardsLayout.setObjectName(u"About_cardsLayout")
        self.About_cardsLayout.setContentsMargins(0, 0, 0, 0)
        self.About_cardModels = QCommandLinkButton(self.About_cards)
        self.About_cardModels.setObjectName(u"About_cardModels")
        self.About_cardModels.setMinimumHeight(120)

        self.About_cardsLayout.addWidget(self.About_cardModels, 0, 0, 1, 1)

        self.About_cardReferences = QCommandLinkButton(self.About_cards)
        self.About_cardReferences.setObjectName(u"About_cardReferences")
        self.About_cardReferences.setMinimumHeight(120)

        self.About_cardsLayout.addWidget(self.About_cardReferences, 0, 1, 1, 1)

        self.About_cardScience = QCommandLinkButton(self.About_cards)
        self.About_cardScience.setObjectName(u"About_cardScience")
        self.About_cardScience.setMinimumHeight(120)

        self.About_cardsLayout.addWidget(self.About_cardScience, 1, 0, 1, 1)

        self.About_cardSoftware = QCommandLinkButton(self.About_cards)
        self.About_cardSoftware.setObjectName(u"About_cardSoftware")
        self.About_cardSoftware.setMinimumHeight(120)

        self.About_cardsLayout.addWidget(self.About_cardSoftware, 1, 1, 1, 1)


        self.About_projectContentsLayout.addWidget(self.About_cards)

        self.About_shortcuts = QWidget(self.About_projectContents)
        self.About_shortcuts.setObjectName(u"About_shortcuts")
        self.About_shortcutsLayout = QHBoxLayout(self.About_shortcuts)
        self.About_shortcutsLayout.setSpacing(12)
        self.About_shortcutsLayout.setObjectName(u"About_shortcutsLayout")
        self.About_shortcutsLayout.setContentsMargins(0, 0, 0, 0)
        self.About_izhShortcut = QPushButton(self.About_shortcuts)
        self.About_izhShortcut.setObjectName(u"About_izhShortcut")
        self.About_izhShortcut.setMinimumHeight(40)

        self.About_shortcutsLayout.addWidget(self.About_izhShortcut)

        self.About_imagingShortcut = QPushButton(self.About_shortcuts)
        self.About_imagingShortcut.setObjectName(u"About_imagingShortcut")
        self.About_imagingShortcut.setMinimumHeight(40)

        self.About_shortcutsLayout.addWidget(self.About_imagingShortcut)


        self.About_projectContentsLayout.addWidget(self.About_shortcuts)

        self.About_creditsBox = QGroupBox(self.About_projectContents)
        self.About_creditsBox.setObjectName(u"About_creditsBox")
        self.About_creditsLayout = QVBoxLayout(self.About_creditsBox)
        self.About_creditsLayout.setSpacing(12)
        self.About_creditsLayout.setObjectName(u"About_creditsLayout")
        self.About_creditsLabel = QLabel(self.About_creditsBox)
        self.About_creditsLabel.setObjectName(u"About_creditsLabel")
        self.About_creditsLabel.setWordWrap(True)
        self.About_creditsLabel.setFont(font2)

        self.About_creditsLayout.addWidget(self.About_creditsLabel)

        self.About_citeProject = QPushButton(self.About_creditsBox)
        self.About_citeProject.setObjectName(u"About_citeProject")
        self.About_citeProject.setMinimumHeight(40)

        self.About_creditsLayout.addWidget(self.About_citeProject)


        self.About_projectContentsLayout.addWidget(self.About_creditsBox)

        self.About_projectStretch = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.About_projectContentsLayout.addItem(self.About_projectStretch)

        self.About_projectScroll.setWidget(self.About_projectContents)

        self.About_projectLayout.addWidget(self.About_projectScroll)

        self.About_stack.addWidget(self.About_projectPage)
        self.About_modelsPage = QWidget()
        self.About_modelsPage.setObjectName(u"About_modelsPage")
        self.About_modelsLayout = QHBoxLayout(self.About_modelsPage)
        self.About_modelsLayout.setSpacing(12)
        self.About_modelsLayout.setObjectName(u"About_modelsLayout")
        self.About_modelSidebar = QWidget(self.About_modelsPage)
        self.About_modelSidebar.setObjectName(u"About_modelSidebar")
        self.About_modelSidebar.setMaximumWidth(270)
        self.About_modelSidebarLayout = QVBoxLayout(self.About_modelSidebar)
        self.About_modelSidebarLayout.setSpacing(12)
        self.About_modelSidebarLayout.setObjectName(u"About_modelSidebarLayout")
        self.About_modelSidebarLayout.setContentsMargins(0, 0, 0, 0)
        self.About_modelSearch = QLineEdit(self.About_modelSidebar)
        self.About_modelSearch.setObjectName(u"About_modelSearch")

        self.About_modelSidebarLayout.addWidget(self.About_modelSearch)

        self.About_modelList = QListWidget(self.About_modelSidebar)
        self.About_modelList.setObjectName(u"About_modelList")

        self.About_modelSidebarLayout.addWidget(self.About_modelList)


        self.About_modelsLayout.addWidget(self.About_modelSidebar)

        self.About_article = QWidget(self.About_modelsPage)
        self.About_article.setObjectName(u"About_article")
        self.About_articleLayout = QVBoxLayout(self.About_article)
        self.About_articleLayout.setSpacing(12)
        self.About_articleLayout.setObjectName(u"About_articleLayout")
        self.About_articleLayout.setContentsMargins(0, 0, 0, 0)
        self.About_articleTitle = QLabel(self.About_article)
        self.About_articleTitle.setObjectName(u"About_articleTitle")
        self.About_articleTitle.setWordWrap(True)
        font7 = QFont()
        font7.setPointSize(17)
        font7.setBold(True)
        self.About_articleTitle.setFont(font7)

        self.About_articleLayout.addWidget(self.About_articleTitle)

        self.About_provenanceLabel = QLabel(self.About_article)
        self.About_provenanceLabel.setObjectName(u"About_provenanceLabel")
        self.About_provenanceLabel.setWordWrap(True)
        self.About_provenanceLabel.setFont(font3)

        self.About_articleLayout.addWidget(self.About_provenanceLabel)

        self.About_articleTabs = QTabWidget(self.About_article)
        self.About_articleTabs.setObjectName(u"About_articleTabs")
        self.About_tabOverview = QWidget()
        self.About_tabOverview.setObjectName(u"About_tabOverview")
        self.About_tabOverviewLayout = QVBoxLayout(self.About_tabOverview)
        self.About_tabOverviewLayout.setSpacing(12)
        self.About_tabOverviewLayout.setObjectName(u"About_tabOverviewLayout")
        self.About_browserOverview = QTextBrowser(self.About_tabOverview)
        self.About_browserOverview.setObjectName(u"About_browserOverview")
        self.About_browserOverview.setOpenExternalLinks(False)
        self.About_browserOverview.setOpenLinks(False)

        self.About_tabOverviewLayout.addWidget(self.About_browserOverview)

        self.About_articleTabs.addTab(self.About_tabOverview, "")
        self.About_tabEquations = QWidget()
        self.About_tabEquations.setObjectName(u"About_tabEquations")
        self.About_tabEquationsLayout = QVBoxLayout(self.About_tabEquations)
        self.About_tabEquationsLayout.setSpacing(12)
        self.About_tabEquationsLayout.setObjectName(u"About_tabEquationsLayout")
        self.About_browserEquations = QTextBrowser(self.About_tabEquations)
        self.About_browserEquations.setObjectName(u"About_browserEquations")
        self.About_browserEquations.setOpenExternalLinks(False)
        self.About_browserEquations.setOpenLinks(False)

        self.About_tabEquationsLayout.addWidget(self.About_browserEquations)

        self.About_articleTabs.addTab(self.About_tabEquations, "")
        self.About_tabImplementation = QWidget()
        self.About_tabImplementation.setObjectName(u"About_tabImplementation")
        self.About_tabImplementationLayout = QVBoxLayout(self.About_tabImplementation)
        self.About_tabImplementationLayout.setSpacing(12)
        self.About_tabImplementationLayout.setObjectName(u"About_tabImplementationLayout")
        self.About_browserImplementation = QTextBrowser(self.About_tabImplementation)
        self.About_browserImplementation.setObjectName(u"About_browserImplementation")
        self.About_browserImplementation.setOpenExternalLinks(False)
        self.About_browserImplementation.setOpenLinks(False)

        self.About_tabImplementationLayout.addWidget(self.About_browserImplementation)

        self.About_articleTabs.addTab(self.About_tabImplementation, "")
        self.About_tabLimitations = QWidget()
        self.About_tabLimitations.setObjectName(u"About_tabLimitations")
        self.About_tabLimitationsLayout = QVBoxLayout(self.About_tabLimitations)
        self.About_tabLimitationsLayout.setSpacing(12)
        self.About_tabLimitationsLayout.setObjectName(u"About_tabLimitationsLayout")
        self.About_browserLimitations = QTextBrowser(self.About_tabLimitations)
        self.About_browserLimitations.setObjectName(u"About_browserLimitations")
        self.About_browserLimitations.setOpenExternalLinks(False)
        self.About_browserLimitations.setOpenLinks(False)

        self.About_tabLimitationsLayout.addWidget(self.About_browserLimitations)

        self.About_articleTabs.addTab(self.About_tabLimitations, "")
        self.About_tabReferences = QWidget()
        self.About_tabReferences.setObjectName(u"About_tabReferences")
        self.About_tabReferencesLayout = QVBoxLayout(self.About_tabReferences)
        self.About_tabReferencesLayout.setSpacing(12)
        self.About_tabReferencesLayout.setObjectName(u"About_tabReferencesLayout")
        self.About_browserReferences = QTextBrowser(self.About_tabReferences)
        self.About_browserReferences.setObjectName(u"About_browserReferences")
        self.About_browserReferences.setOpenExternalLinks(False)
        self.About_browserReferences.setOpenLinks(False)

        self.About_tabReferencesLayout.addWidget(self.About_browserReferences)

        self.About_articleTabs.addTab(self.About_tabReferences, "")

        self.About_articleLayout.addWidget(self.About_articleTabs)

        self.About_viewSource = QPushButton(self.About_article)
        self.About_viewSource.setObjectName(u"About_viewSource")
        self.About_viewSource.setMinimumHeight(40)

        self.About_articleLayout.addWidget(self.About_viewSource)


        self.About_modelsLayout.addWidget(self.About_article)

        self.About_stack.addWidget(self.About_modelsPage)
        self.About_referencesPage = QWidget()
        self.About_referencesPage.setObjectName(u"About_referencesPage")
        self.About_referencesLayout = QVBoxLayout(self.About_referencesPage)
        self.About_referencesLayout.setSpacing(12)
        self.About_referencesLayout.setObjectName(u"About_referencesLayout")
        self.About_referenceSearch = QLineEdit(self.About_referencesPage)
        self.About_referenceSearch.setObjectName(u"About_referenceSearch")

        self.About_referencesLayout.addWidget(self.About_referenceSearch)

        self.About_referenceSplitter = QSplitter(self.About_referencesPage)
        self.About_referenceSplitter.setObjectName(u"About_referenceSplitter")
        self.About_referenceSplitter.setOrientation(Qt.Horizontal)
        self.About_referenceList = QListWidget(self.About_referenceSplitter)
        self.About_referenceList.setObjectName(u"About_referenceList")
        self.About_referenceSplitter.addWidget(self.About_referenceList)
        self.About_referenceDetail = QTextBrowser(self.About_referenceSplitter)
        self.About_referenceDetail.setObjectName(u"About_referenceDetail")
        self.About_referenceSplitter.addWidget(self.About_referenceDetail)

        self.About_referencesLayout.addWidget(self.About_referenceSplitter)

        self.About_referenceActions = QWidget(self.About_referencesPage)
        self.About_referenceActions.setObjectName(u"About_referenceActions")
        self.About_referenceActionsLayout = QHBoxLayout(self.About_referenceActions)
        self.About_referenceActionsLayout.setSpacing(12)
        self.About_referenceActionsLayout.setObjectName(u"About_referenceActionsLayout")
        self.About_referenceActionsLayout.setContentsMargins(0, 0, 0, 0)
        self.About_OpenPaper = QPushButton(self.About_referenceActions)
        self.About_OpenPaper.setObjectName(u"About_OpenPaper")
        self.About_OpenPaper.setMinimumHeight(40)

        self.About_referenceActionsLayout.addWidget(self.About_OpenPaper)

        self.About_CopyCitation = QPushButton(self.About_referenceActions)
        self.About_CopyCitation.setObjectName(u"About_CopyCitation")
        self.About_CopyCitation.setMinimumHeight(40)

        self.About_referenceActionsLayout.addWidget(self.About_CopyCitation)

        self.About_CopyBibtex = QPushButton(self.About_referenceActions)
        self.About_CopyBibtex.setObjectName(u"About_CopyBibtex")
        self.About_CopyBibtex.setMinimumHeight(40)

        self.About_referenceActionsLayout.addWidget(self.About_CopyBibtex)


        self.About_referencesLayout.addWidget(self.About_referenceActions)

        self.About_stack.addWidget(self.About_referencesPage)
        self.About_sciencePage = QWidget()
        self.About_sciencePage.setObjectName(u"About_sciencePage")
        self.About_scienceLayout = QVBoxLayout(self.About_sciencePage)
        self.About_scienceLayout.setSpacing(12)
        self.About_scienceLayout.setObjectName(u"About_scienceLayout")
        self.About_scienceBrowser = QTextBrowser(self.About_sciencePage)
        self.About_scienceBrowser.setObjectName(u"About_scienceBrowser")
        self.About_scienceBrowser.setOpenExternalLinks(False)
        self.About_scienceBrowser.setOpenLinks(False)

        self.About_scienceLayout.addWidget(self.About_scienceBrowser)

        self.About_scienceActions = QWidget(self.About_sciencePage)
        self.About_scienceActions.setObjectName(u"About_scienceActions")
        self.About_scienceActionsLayout = QHBoxLayout(self.About_scienceActions)
        self.About_scienceActionsLayout.setSpacing(12)
        self.About_scienceActionsLayout.setObjectName(u"About_scienceActionsLayout")
        self.About_scienceActionsLayout.setContentsMargins(0, 0, 0, 0)
        self.About_Repository = QPushButton(self.About_scienceActions)
        self.About_Repository.setObjectName(u"About_Repository")
        self.About_Repository.setMinimumHeight(40)

        self.About_scienceActionsLayout.addWidget(self.About_Repository)

        self.About_Issues = QPushButton(self.About_scienceActions)
        self.About_Issues.setObjectName(u"About_Issues")
        self.About_Issues.setMinimumHeight(40)

        self.About_scienceActionsLayout.addWidget(self.About_Issues)

        self.About_SoftwareLicence = QPushButton(self.About_scienceActions)
        self.About_SoftwareLicence.setObjectName(u"About_SoftwareLicence")
        self.About_SoftwareLicence.setMinimumHeight(40)

        self.About_scienceActionsLayout.addWidget(self.About_SoftwareLicence)

        self.About_HardwareLicence = QPushButton(self.About_scienceActions)
        self.About_HardwareLicence.setObjectName(u"About_HardwareLicence")
        self.About_HardwareLicence.setMinimumHeight(40)

        self.About_scienceActionsLayout.addWidget(self.About_HardwareLicence)


        self.About_scienceLayout.addWidget(self.About_scienceActions)

        self.About_stack.addWidget(self.About_sciencePage)
        self.About_softwarePage = QWidget()
        self.About_softwarePage.setObjectName(u"About_softwarePage")
        self.About_softwareLayout = QVBoxLayout(self.About_softwarePage)
        self.About_softwareLayout.setSpacing(12)
        self.About_softwareLayout.setObjectName(u"About_softwareLayout")
        self.About_softwareTitle = QLabel(self.About_softwarePage)
        self.About_softwareTitle.setObjectName(u"About_softwareTitle")
        self.About_softwareTitle.setWordWrap(True)
        self.About_softwareTitle.setFont(font7)

        self.About_softwareLayout.addWidget(self.About_softwareTitle)

        self.About_deviceNote = QLabel(self.About_softwarePage)
        self.About_deviceNote.setObjectName(u"About_deviceNote")
        self.About_deviceNote.setWordWrap(True)
        self.About_deviceNote.setFont(font2)

        self.About_softwareLayout.addWidget(self.About_deviceNote)

        self.About_diagnostics = QPlainTextEdit(self.About_softwarePage)
        self.About_diagnostics.setObjectName(u"About_diagnostics")
        self.About_diagnostics.setReadOnly(True)

        self.About_softwareLayout.addWidget(self.About_diagnostics)

        self.About_softwareActions = QWidget(self.About_softwarePage)
        self.About_softwareActions.setObjectName(u"About_softwareActions")
        self.About_softwareActionsLayout = QHBoxLayout(self.About_softwareActions)
        self.About_softwareActionsLayout.setSpacing(12)
        self.About_softwareActionsLayout.setObjectName(u"About_softwareActionsLayout")
        self.About_softwareActionsLayout.setContentsMargins(0, 0, 0, 0)
        self.About_RefreshInfo = QPushButton(self.About_softwareActions)
        self.About_RefreshInfo.setObjectName(u"About_RefreshInfo")
        self.About_RefreshInfo.setMinimumHeight(40)

        self.About_softwareActionsLayout.addWidget(self.About_RefreshInfo)

        self.About_CopyInfo = QPushButton(self.About_softwareActions)
        self.About_CopyInfo.setObjectName(u"About_CopyInfo")
        self.About_CopyInfo.setMinimumHeight(40)

        self.About_softwareActionsLayout.addWidget(self.About_CopyInfo)

        self.About_Updates = QPushButton(self.About_softwareActions)
        self.About_Updates.setObjectName(u"About_Updates")
        self.About_Updates.setMinimumHeight(40)

        self.About_softwareActionsLayout.addWidget(self.About_Updates)


        self.About_softwareLayout.addWidget(self.About_softwareActions)

        self.About_stack.addWidget(self.About_softwarePage)

        self.About_rootLayout.addWidget(self.About_stack)

        self.About_footer = QWidget(AboutPanel)
        self.About_footer.setObjectName(u"About_footer")
        self.About_footerLayout = QHBoxLayout(self.About_footer)
        self.About_footerLayout.setSpacing(12)
        self.About_footerLayout.setObjectName(u"About_footerLayout")
        self.About_footerLayout.setContentsMargins(0, 0, 0, 0)
        self.About_footerLabel = QLabel(self.About_footer)
        self.About_footerLabel.setObjectName(u"About_footerLabel")
        self.About_footerLabel.setWordWrap(True)
        self.About_footerLabel.setFont(font2)

        self.About_footerLayout.addWidget(self.About_footerLabel)

        self.About_Website = QPushButton(self.About_footer)
        self.About_Website.setObjectName(u"About_Website")
        self.About_Website.setMinimumHeight(40)

        self.About_footerLayout.addWidget(self.About_Website)

        self.About_Documentation = QPushButton(self.About_footer)
        self.About_Documentation.setObjectName(u"About_Documentation")
        self.About_Documentation.setMinimumHeight(40)

        self.About_footerLayout.addWidget(self.About_Documentation)

        self.About_versionLabel = QLabel(self.About_footer)
        self.About_versionLabel.setObjectName(u"About_versionLabel")
        self.About_versionLabel.setWordWrap(True)
        self.About_versionLabel.setFont(font2)

        self.About_footerLayout.addWidget(self.About_versionLabel)


        self.About_rootLayout.addWidget(self.About_footer)

        self.About_statusLabel = QLabel(AboutPanel)
        self.About_statusLabel.setObjectName(u"About_statusLabel")
        self.About_statusLabel.setWordWrap(True)
        self.About_statusLabel.setFont(font3)

        self.About_rootLayout.addWidget(self.About_statusLabel)


        self.retranslateUi(AboutPanel)

        self.About_stack.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(AboutPanel)
    # setupUi

    def retranslateUi(self, AboutPanel):
        AboutPanel.setWindowTitle(QCoreApplication.translate("AboutPanel", u"About & Scientific foundations", None))
        self.About_titleLabel.setText(QCoreApplication.translate("AboutPanel", u"About & Scientific foundations", None))
        self.About_subtitleLabel.setText(QCoreApplication.translate("AboutPanel", u"Understand the science. Explore the models. Reproduce the experiment.", None))
        self.About_navProject.setText(QCoreApplication.translate("AboutPanel", u"The project", None))
        self.About_navModels.setText(QCoreApplication.translate("AboutPanel", u"Models && methods", None))
        self.About_navReferences.setText(QCoreApplication.translate("AboutPanel", u"References", None))
        self.About_navScience.setText(QCoreApplication.translate("AboutPanel", u"Open science", None))
        self.About_navSoftware.setText(QCoreApplication.translate("AboutPanel", u"Software && device", None))
        self.About_breadcrumbLabel.setText(QCoreApplication.translate("AboutPanel", u"About / The project", None))
        self.About_heroBox.setTitle(QCoreApplication.translate("AboutPanel", u"Spikeling", None))
        self.About_missionLabel.setText(QCoreApplication.translate("AboutPanel", u"An open-source platform for teaching neurophysiology, experimental design and neural data analysis.", None))
        self.About_introLabel.setText(QCoreApplication.translate("AboutPanel", u"Connect neuronal models with hands-on experimentation: design stimuli, observe activity, record experiments and interpret data. Spikeling combines open hardware, firmware and desktop software for education and outreach.", None))
        self.About_exploreLabel.setText(QCoreApplication.translate("AboutPanel", u"Explore the scientific foundations", None))
        self.About_cardModels.setText(QCoreApplication.translate("AboutPanel", u"Models && methods", None))
        self.About_cardModels.setDescription(QCoreApplication.translate("AboutPanel", u"Neuron dynamics, synapses, clamp modes and imaging.\n"
"Explore the models \u2192", None))
        self.About_cardReferences.setText(QCoreApplication.translate("AboutPanel", u"References", None))
        self.About_cardReferences.setDescription(QCoreApplication.translate("AboutPanel", u"Find the papers behind the models and methods.\n"
"Browse papers \u2192", None))
        self.About_cardScience.setText(QCoreApplication.translate("AboutPanel", u"Open science", None))
        self.About_cardScience.setDescription(QCoreApplication.translate("AboutPanel", u"Source code, licences and reproducibility.\n"
"Explore the project \u2192", None))
        self.About_cardSoftware.setText(QCoreApplication.translate("AboutPanel", u"Software && device", None))
        self.About_cardSoftware.setDescription(QCoreApplication.translate("AboutPanel", u"Versions, compatibility and diagnostic details.\n"
"View information \u2192", None))
        self.About_izhShortcut.setText(QCoreApplication.translate("AboutPanel", u"Izhikevich model \u2192", None))
        self.About_imagingShortcut.setText(QCoreApplication.translate("AboutPanel", u"Calcium && fluorescence \u2192", None))
        self.About_creditsBox.setTitle(QCoreApplication.translate("AboutPanel", u"People && origins", None))
        self.About_creditsLabel.setText(QCoreApplication.translate("AboutPanel", u"Developed by M. J. Y. Zimmermann\n"
"Maintained by P. Rignanese and A. Koumoundourou\n"
"Based on an original idea by T. Baden\n"
"Open Source Neuro \u2014 open tools for neuroscience education and outreach.", None))
        self.About_citeProject.setText(QCoreApplication.translate("AboutPanel", u"Cite Spikeling \u2192", None))
        self.About_modelSearch.setPlaceholderText(QCoreApplication.translate("AboutPanel", u"Find a model or method\u2026", None))
#if QT_CONFIG(accessibility)
        self.About_modelSearch.setAccessibleName(QCoreApplication.translate("AboutPanel", u"Find a model or method", None))
#endif // QT_CONFIG(accessibility)
        self.About_articleTitle.setText(QCoreApplication.translate("AboutPanel", u"Neuron dynamics", None))
        self.About_provenanceLabel.setText(QCoreApplication.translate("AboutPanel", u"Model provenance", None))
        self.About_articleTabs.setTabText(self.About_articleTabs.indexOf(self.About_tabOverview), QCoreApplication.translate("AboutPanel", u"Overview", None))
        self.About_articleTabs.setTabText(self.About_articleTabs.indexOf(self.About_tabEquations), QCoreApplication.translate("AboutPanel", u"Equations", None))
        self.About_articleTabs.setTabText(self.About_articleTabs.indexOf(self.About_tabImplementation), QCoreApplication.translate("AboutPanel", u"Implementation", None))
        self.About_articleTabs.setTabText(self.About_articleTabs.indexOf(self.About_tabLimitations), QCoreApplication.translate("AboutPanel", u"Limitations", None))
        self.About_articleTabs.setTabText(self.About_articleTabs.indexOf(self.About_tabReferences), QCoreApplication.translate("AboutPanel", u"References", None))
        self.About_viewSource.setText(QCoreApplication.translate("AboutPanel", u"View implementation \u2197", None))
        self.About_referenceSearch.setPlaceholderText(QCoreApplication.translate("AboutPanel", u"Search authors, titles, years or DOI\u2026", None))
#if QT_CONFIG(accessibility)
        self.About_referenceSearch.setAccessibleName(QCoreApplication.translate("AboutPanel", u"Search references", None))
#endif // QT_CONFIG(accessibility)
        self.About_OpenPaper.setText(QCoreApplication.translate("AboutPanel", u"Read publication \u2197", None))
        self.About_CopyCitation.setText(QCoreApplication.translate("AboutPanel", u"Copy citation", None))
        self.About_CopyBibtex.setText(QCoreApplication.translate("AboutPanel", u"Copy BibTeX", None))
        self.About_Repository.setText(QCoreApplication.translate("AboutPanel", u"Source code \u2197", None))
        self.About_Issues.setText(QCoreApplication.translate("AboutPanel", u"Report an issue \u2197", None))
        self.About_SoftwareLicence.setText(QCoreApplication.translate("AboutPanel", u"Software licence \u2197", None))
        self.About_HardwareLicence.setText(QCoreApplication.translate("AboutPanel", u"Hardware licence \u2197", None))
        self.About_softwareTitle.setText(QCoreApplication.translate("AboutPanel", u"Software & device information", None))
        self.About_deviceNote.setText(QCoreApplication.translate("AboutPanel", u"This report reads existing connection information. It does not open a port or send commands to the board.", None))
        self.About_RefreshInfo.setText(QCoreApplication.translate("AboutPanel", u"Refresh information", None))
        self.About_CopyInfo.setText(QCoreApplication.translate("AboutPanel", u"Copy version information", None))
        self.About_Updates.setText(QCoreApplication.translate("AboutPanel", u"Updates && releases \u2197", None))
        self.About_footerLabel.setText(QCoreApplication.translate("AboutPanel", u"Open Source Neuro", None))
        self.About_Website.setText(QCoreApplication.translate("AboutPanel", u"Project website \u2197", None))
        self.About_Documentation.setText(QCoreApplication.translate("AboutPanel", u"Documentation \u2197", None))
        self.About_versionLabel.setText(QCoreApplication.translate("AboutPanel", u"GUI version", None))
        self.About_statusLabel.setText("")
    # retranslateUi

