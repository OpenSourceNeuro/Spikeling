# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Spikeling_SplashScreen.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QProgressBar, QSizePolicy, QVBoxLayout,
    QWidget)
import resources_rc

class Ui_SplashScreen(object):
    def setupUi(self, SplashScreen):
        if not SplashScreen.objectName():
            SplashScreen.setObjectName(u"SplashScreen")
        SplashScreen.resize(1314, 759)
        SplashScreen.setStyleSheet(u"QFrame{\n"
"	background-color: rgb(0, 30, 38);\n"
"	color: rgb(147, 161, 161);\n"
"	border-radius: 25px\n"
"}\n"
"\n"
"QProgressBar{\n"
"	background-color: rgb(0, 43, 54);\n"
"	color: rgb(147, 161, 161);\n"
"	border-style: none;\n"
"	border-radius: 10px;\n"
"	text-align: center;\n"
"}\n"
"\n"
"QProgressBar::chunk{\n"
"	background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(38, 139, 210, 255), stop:1 rgba(42, 161, 152, 255));\n"
"	border-radius: 10px;\n"
"}")
        self.centralwidget = QWidget(SplashScreen)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.SplashFrame = QFrame(self.centralwidget)
        self.SplashFrame.setObjectName(u"SplashFrame")
        self.SplashFrame.setStyleSheet(u"")
        self.SplashFrame.setFrameShape(QFrame.StyledPanel)
        self.SplashFrame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.SplashFrame)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(15, 15, 15, 15)
        self.Header_Frame = QFrame(self.SplashFrame)
        self.Header_Frame.setObjectName(u"Header_Frame")
        self.Header_Frame.setMinimumSize(QSize(0, 200))
        self.Header_Frame.setMaximumSize(QSize(16777215, 200))
        self.Header_Frame.setFrameShape(QFrame.StyledPanel)
        self.Header_Frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.Header_Frame)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(self.Header_Frame)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")
        self.label.setMaximumSize(QSize(316, 200))
        self.label.setPixmap(QPixmap(u":/resources/resources/SpikyLogo.png"))
        self.label.setScaledContents(True)

        self.horizontalLayout_2.addWidget(self.label, 0, Qt.AlignLeft)


        self.horizontalLayout.addWidget(self.frame, 0, Qt.AlignLeft|Qt.AlignTop)


        self.verticalLayout_5.addWidget(self.Header_Frame)

        self.Status_Frame = QFrame(self.SplashFrame)
        self.Status_Frame.setObjectName(u"Status_Frame")
        self.Status_Frame.setFrameShape(QFrame.StyledPanel)
        self.Status_Frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.Status_Frame)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 100)
        self.label_3 = QLabel(self.Status_Frame)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout_6.addWidget(self.label_3, 0, Qt.AlignTop)


        self.verticalLayout_5.addWidget(self.Status_Frame, 0, Qt.AlignTop)

        self.Loading_Frame = QFrame(self.SplashFrame)
        self.Loading_Frame.setObjectName(u"Loading_Frame")
        self.Loading_Frame.setMinimumSize(QSize(0, 0))
        self.Loading_Frame.setMaximumSize(QSize(16777215, 100))
        self.Loading_Frame.setFrameShape(QFrame.StyledPanel)
        self.Loading_Frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.Loading_Frame)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(50, 50, 50, 0)
        self.Loading_ProgressBar = QProgressBar(self.Loading_Frame)
        self.Loading_ProgressBar.setObjectName(u"Loading_ProgressBar")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.Loading_ProgressBar.setFont(font)
        self.Loading_ProgressBar.setValue(24)

        self.verticalLayout_2.addWidget(self.Loading_ProgressBar)


        self.verticalLayout_5.addWidget(self.Loading_Frame)

        self.frame_2 = QFrame(self.SplashFrame)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_6 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.Status_Label = QLabel(self.frame_2)
        self.Status_Label.setObjectName(u"Status_Label")
        font1 = QFont()
        font1.setPointSize(18)
        self.Status_Label.setFont(font1)
        self.Status_Label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_6.addWidget(self.Status_Label, 0, Qt.AlignTop)


        self.verticalLayout_5.addWidget(self.frame_2)

        self.Footer_Frame = QFrame(self.SplashFrame)
        self.Footer_Frame.setObjectName(u"Footer_Frame")
        self.Footer_Frame.setFrameShape(QFrame.StyledPanel)
        self.Footer_Frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.Footer_Frame)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.License_Frame = QFrame(self.Footer_Frame)
        self.License_Frame.setObjectName(u"License_Frame")
        self.License_Frame.setMinimumSize(QSize(0, 100))
        self.License_Frame.setMaximumSize(QSize(500, 16777215))
        self.License_Frame.setFrameShape(QFrame.StyledPanel)
        self.License_Frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.License_Frame)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label_2 = QLabel(self.License_Frame)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_4.addWidget(self.label_2, 0, Qt.AlignBottom)


        self.horizontalLayout_3.addWidget(self.License_Frame, 0, Qt.AlignBottom)

        self.Logo_Frame = QFrame(self.Footer_Frame)
        self.Logo_Frame.setObjectName(u"Logo_Frame")
        self.Logo_Frame.setMinimumSize(QSize(0, 100))
        self.Logo_Frame.setFrameShape(QFrame.StyledPanel)
        self.Logo_Frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.Logo_Frame)
        self.horizontalLayout_5.setSpacing(20)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.Sussex_Logo = QLabel(self.Logo_Frame)
        self.Sussex_Logo.setObjectName(u"Sussex_Logo")
        self.Sussex_Logo.setMinimumSize(QSize(236, 75))
        self.Sussex_Logo.setMaximumSize(QSize(236, 75))
        self.Sussex_Logo.setPixmap(QPixmap(u":/resources/resources/SN-Logo.png"))
        self.Sussex_Logo.setScaledContents(True)

        self.horizontalLayout_5.addWidget(self.Sussex_Logo, 0, Qt.AlignVCenter)

        self.TReND_Logo = QLabel(self.Logo_Frame)
        self.TReND_Logo.setObjectName(u"TReND_Logo")
        self.TReND_Logo.setMinimumSize(QSize(113, 100))
        self.TReND_Logo.setMaximumSize(QSize(113, 100))
        self.TReND_Logo.setPixmap(QPixmap(u":/resources/resources/CaMinA.png"))
        self.TReND_Logo.setScaledContents(True)

        self.horizontalLayout_5.addWidget(self.TReND_Logo)


        self.horizontalLayout_3.addWidget(self.Logo_Frame, 0, Qt.AlignHCenter|Qt.AlignBottom)

        self.Credits_Frame = QFrame(self.Footer_Frame)
        self.Credits_Frame.setObjectName(u"Credits_Frame")
        self.Credits_Frame.setMinimumSize(QSize(0, 100))
        self.Credits_Frame.setMaximumSize(QSize(500, 100))
        self.Credits_Frame.setFrameShape(QFrame.StyledPanel)
        self.Credits_Frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.Credits_Frame)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.Credits_Label = QLabel(self.Credits_Frame)
        self.Credits_Label.setObjectName(u"Credits_Label")
        self.Credits_Label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.verticalLayout_3.addWidget(self.Credits_Label)


        self.horizontalLayout_3.addWidget(self.Credits_Frame)


        self.verticalLayout_5.addWidget(self.Footer_Frame, 0, Qt.AlignBottom)


        self.verticalLayout.addWidget(self.SplashFrame)

        SplashScreen.setCentralWidget(self.centralwidget)

        self.retranslateUi(SplashScreen)

        QMetaObject.connectSlotsByName(SplashScreen)
    # setupUi

    def retranslateUi(self, SplashScreen):
        SplashScreen.setWindowTitle(QCoreApplication.translate("SplashScreen", u"MainWindow", None))
        self.label.setText("")
#if QT_CONFIG(whatsthis)
        self.label_3.setWhatsThis(QCoreApplication.translate("SplashScreen", u"<html><head/><body><p align=\"center\"><span style=\" font-size:48pt; color:#93a1a1;\">Spikeling </span><span style=\" font-size:28pt; color:#93a1a1;\">v2.2</span></p><p align=\"center\"><span style=\" font-size:18pt; color:#93a1a1;\">a Hardware implementation of spiking neurons</span></p><p align=\"center\"><span style=\" font-size:18pt; color:#93a1a1;\">for neuroscience teaching and outreach</span></p></body></html>", None))
#endif // QT_CONFIG(whatsthis)
        self.label_3.setText(QCoreApplication.translate("SplashScreen", u"<html><head/><body><p align=\"center\"><span style=\" font-size:72pt; color:#93a1a1;\">Spikeling </span><span style=\" font-size:16pt; color:#93a1a1;\">v2.4</span></p><p align=\"center\"><span style=\" font-size:18pt; color:#93a1a1;\">A hardware implementation of spiking neurons for neuroscience teaching and outreach</span></p></body></html>", None))
        self.Status_Label.setText(QCoreApplication.translate("SplashScreen", u"Welcome to Spikeling GUI", None))
        self.label_2.setText(QCoreApplication.translate("SplashScreen", u"<html><head/><body><p><span style=\" font-size:10pt;\">This project is licensed under the GNU General Public License v3.0</span></p></body></html>", None))
        self.Sussex_Logo.setText("")
        self.TReND_Logo.setText("")
        self.Credits_Label.setText(QCoreApplication.translate("SplashScreen", u"<html><head/><body><p><span style=\" font-size:10pt; font-weight:600;\">Developped by </span><span style=\" font-size:10pt;\">M.J.Y. Zimmermann</span></p><p><span style=\" font-size:10pt; font-weight:600;\">Based on</span><span style=\" font-size:10pt;\"> an original idea by T. Baden</span></p></body></html>", None))
    # retranslateUi

