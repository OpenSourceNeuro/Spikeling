# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Neuron_Parameters.ui'
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
    QLineEdit, QMainWindow, QPushButton, QSizePolicy,
    QStatusBar, QVBoxLayout, QWidget)

class Ui_AdvancedParameters(object):
    def setupUi(self, AdvancedParameters):
        if not AdvancedParameters.objectName():
            AdvancedParameters.setObjectName(u"AdvancedParameters")
        AdvancedParameters.resize(400, 760)
        AdvancedParameters.setStyleSheet(u"*{\n"
"	border:none;\n"
"	background-color:rgb(0, 43, 54);  \n"
"	padding: 0;\n"
"	margin:0;\n"
"	color: rgb(147,161,161);    \n"
"}\n"
"\n"
"* QPushButton{\n"
"	text-align: left;\n"
"	padding: 10px 5px;\n"
"	border-radius:20px;\n"
"	background-color: rgb(7, 54, 66);\n"
"    border: 1px solid rgb(147,161,161);\n"
"}\n"
"* QPushButton:hover{\n"
"	background-color: rgb(0, 30, 38);\n"
"}\n"
"\n"
"* QLineEdit{\n"
"	border: 2px solid rgb(147,161,161);\n"
"    background-color: rgb(7, 54, 66);\n"
"}\n"
"\n"
"\n"
"")
        self.centralwidget = QWidget(AdvancedParameters)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.AdvancedParameters_frame = QFrame(self.centralwidget)
        self.AdvancedParameters_frame.setObjectName(u"AdvancedParameters_frame")
        self.AdvancedParameters_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.AdvancedParameters_frame)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Title_frame = QFrame(self.AdvancedParameters_frame)
        self.AdvancedParameters_Title_frame.setObjectName(u"AdvancedParameters_Title_frame")
        self.AdvancedParameters_Title_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_Title_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.AdvancedParameters_Title_frame)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Title_label = QLabel(self.AdvancedParameters_Title_frame)
        self.AdvancedParameters_Title_label.setObjectName(u"AdvancedParameters_Title_label")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.AdvancedParameters_Title_label.setFont(font)

        self.verticalLayout_4.addWidget(self.AdvancedParameters_Title_label, 0, Qt.AlignHCenter)


        self.verticalLayout_2.addWidget(self.AdvancedParameters_Title_frame)

        self.AdvancedParameters_lineEdit_frame = QFrame(self.AdvancedParameters_frame)
        self.AdvancedParameters_lineEdit_frame.setObjectName(u"AdvancedParameters_lineEdit_frame")
        self.AdvancedParameters_lineEdit_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_lineEdit_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.AdvancedParameters_lineEdit_frame)
        self.verticalLayout_3.setSpacing(20)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(5, 0, 5, 0)
        self.AdvancedParameters_PRGain_frame = QFrame(self.AdvancedParameters_lineEdit_frame)
        self.AdvancedParameters_PRGain_frame.setObjectName(u"AdvancedParameters_PRGain_frame")
        self.AdvancedParameters_PRGain_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_PRGain_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.AdvancedParameters_PRGain_frame)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_PRGain_label_frame = QFrame(self.AdvancedParameters_PRGain_frame)
        self.AdvancedParameters_PRGain_label_frame.setObjectName(u"AdvancedParameters_PRGain_label_frame")
        self.AdvancedParameters_PRGain_label_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_PRGain_label_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_7 = QVBoxLayout(self.AdvancedParameters_PRGain_label_frame)
        self.verticalLayout_7.setSpacing(0)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_PRGain_label = QLabel(self.AdvancedParameters_PRGain_label_frame)
        self.AdvancedParameters_PRGain_label.setObjectName(u"AdvancedParameters_PRGain_label")
        font1 = QFont()
        font1.setPointSize(12)
        self.AdvancedParameters_PRGain_label.setFont(font1)

        self.verticalLayout_7.addWidget(self.AdvancedParameters_PRGain_label)


        self.horizontalLayout_2.addWidget(self.AdvancedParameters_PRGain_label_frame)

        self.AdvancedParameters_PRGain_lineEdit_frame = QFrame(self.AdvancedParameters_PRGain_frame)
        self.AdvancedParameters_PRGain_lineEdit_frame.setObjectName(u"AdvancedParameters_PRGain_lineEdit_frame")
        self.AdvancedParameters_PRGain_lineEdit_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_PRGain_lineEdit_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_12 = QVBoxLayout(self.AdvancedParameters_PRGain_lineEdit_frame)
        self.verticalLayout_12.setSpacing(0)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalLayout_12.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_PRGain_lineEdit = QLineEdit(self.AdvancedParameters_PRGain_lineEdit_frame)
        self.AdvancedParameters_PRGain_lineEdit.setObjectName(u"AdvancedParameters_PRGain_lineEdit")
        self.AdvancedParameters_PRGain_lineEdit.setMaximumSize(QSize(100, 16777215))
        font2 = QFont()
        font2.setPointSize(12)
        font2.setBold(True)
        self.AdvancedParameters_PRGain_lineEdit.setFont(font2)
        self.AdvancedParameters_PRGain_lineEdit.setAlignment(Qt.AlignCenter)

        self.verticalLayout_12.addWidget(self.AdvancedParameters_PRGain_lineEdit, 0, Qt.AlignRight)


        self.horizontalLayout_2.addWidget(self.AdvancedParameters_PRGain_lineEdit_frame)


        self.verticalLayout_3.addWidget(self.AdvancedParameters_PRGain_frame)

        self.AdvancedParameters_PRDecay_frame = QFrame(self.AdvancedParameters_lineEdit_frame)
        self.AdvancedParameters_PRDecay_frame.setObjectName(u"AdvancedParameters_PRDecay_frame")
        self.AdvancedParameters_PRDecay_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_PRDecay_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.AdvancedParameters_PRDecay_frame)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_PRDecay_label_frame = QFrame(self.AdvancedParameters_PRDecay_frame)
        self.AdvancedParameters_PRDecay_label_frame.setObjectName(u"AdvancedParameters_PRDecay_label_frame")
        self.AdvancedParameters_PRDecay_label_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_PRDecay_label_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.AdvancedParameters_PRDecay_label_frame)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_PRDecay_label = QLabel(self.AdvancedParameters_PRDecay_label_frame)
        self.AdvancedParameters_PRDecay_label.setObjectName(u"AdvancedParameters_PRDecay_label")
        self.AdvancedParameters_PRDecay_label.setFont(font1)

        self.verticalLayout_6.addWidget(self.AdvancedParameters_PRDecay_label)


        self.horizontalLayout_3.addWidget(self.AdvancedParameters_PRDecay_label_frame)

        self.AdvancedParameters_PRDecay_lineEdit_frame = QFrame(self.AdvancedParameters_PRDecay_frame)
        self.AdvancedParameters_PRDecay_lineEdit_frame.setObjectName(u"AdvancedParameters_PRDecay_lineEdit_frame")
        self.AdvancedParameters_PRDecay_lineEdit_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_PRDecay_lineEdit_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_8 = QHBoxLayout(self.AdvancedParameters_PRDecay_lineEdit_frame)
        self.horizontalLayout_8.setSpacing(0)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_PRDecay_lineEdit = QLineEdit(self.AdvancedParameters_PRDecay_lineEdit_frame)
        self.AdvancedParameters_PRDecay_lineEdit.setObjectName(u"AdvancedParameters_PRDecay_lineEdit")
        self.AdvancedParameters_PRDecay_lineEdit.setMaximumSize(QSize(100, 16777215))
        self.AdvancedParameters_PRDecay_lineEdit.setFont(font2)
        self.AdvancedParameters_PRDecay_lineEdit.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_8.addWidget(self.AdvancedParameters_PRDecay_lineEdit, 0, Qt.AlignRight)


        self.horizontalLayout_3.addWidget(self.AdvancedParameters_PRDecay_lineEdit_frame)


        self.verticalLayout_3.addWidget(self.AdvancedParameters_PRDecay_frame)

        self.AdvancedParameters_PRRecovery_frame = QFrame(self.AdvancedParameters_lineEdit_frame)
        self.AdvancedParameters_PRRecovery_frame.setObjectName(u"AdvancedParameters_PRRecovery_frame")
        self.AdvancedParameters_PRRecovery_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_PRRecovery_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.AdvancedParameters_PRRecovery_frame)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_PRRecovery_label_frame = QFrame(self.AdvancedParameters_PRRecovery_frame)
        self.AdvancedParameters_PRRecovery_label_frame.setObjectName(u"AdvancedParameters_PRRecovery_label_frame")
        self.AdvancedParameters_PRRecovery_label_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_PRRecovery_label_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.AdvancedParameters_PRRecovery_label_frame)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_PRRecovery_label = QLabel(self.AdvancedParameters_PRRecovery_label_frame)
        self.AdvancedParameters_PRRecovery_label.setObjectName(u"AdvancedParameters_PRRecovery_label")
        self.AdvancedParameters_PRRecovery_label.setFont(font1)

        self.verticalLayout_5.addWidget(self.AdvancedParameters_PRRecovery_label)


        self.horizontalLayout_4.addWidget(self.AdvancedParameters_PRRecovery_label_frame)

        self.AdvancedParameters_PRRecovery_lineEdit_frame = QFrame(self.AdvancedParameters_PRRecovery_frame)
        self.AdvancedParameters_PRRecovery_lineEdit_frame.setObjectName(u"AdvancedParameters_PRRecovery_lineEdit_frame")
        self.AdvancedParameters_PRRecovery_lineEdit_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_PRRecovery_lineEdit_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_13 = QVBoxLayout(self.AdvancedParameters_PRRecovery_lineEdit_frame)
        self.verticalLayout_13.setSpacing(0)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.verticalLayout_13.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_PRRecovery_lineEdit = QLineEdit(self.AdvancedParameters_PRRecovery_lineEdit_frame)
        self.AdvancedParameters_PRRecovery_lineEdit.setObjectName(u"AdvancedParameters_PRRecovery_lineEdit")
        self.AdvancedParameters_PRRecovery_lineEdit.setMaximumSize(QSize(100, 16777215))
        self.AdvancedParameters_PRRecovery_lineEdit.setFont(font2)
        self.AdvancedParameters_PRRecovery_lineEdit.setAlignment(Qt.AlignCenter)

        self.verticalLayout_13.addWidget(self.AdvancedParameters_PRRecovery_lineEdit, 0, Qt.AlignRight)


        self.horizontalLayout_4.addWidget(self.AdvancedParameters_PRRecovery_lineEdit_frame)


        self.verticalLayout_3.addWidget(self.AdvancedParameters_PRRecovery_frame)

        self.Space_frame1 = QFrame(self.AdvancedParameters_lineEdit_frame)
        self.Space_frame1.setObjectName(u"Space_frame1")
        self.Space_frame1.setFrameShape(QFrame.StyledPanel)
        self.Space_frame1.setFrameShadow(QFrame.Raised)
        self.verticalLayout_21 = QVBoxLayout(self.Space_frame1)
        self.verticalLayout_21.setSpacing(5)
        self.verticalLayout_21.setObjectName(u"verticalLayout_21")
        self.verticalLayout_21.setContentsMargins(5, 5, 0, 5)

        self.verticalLayout_3.addWidget(self.Space_frame1)

        self.AdvancedParameters_Syn1Gain_frame = QFrame(self.AdvancedParameters_lineEdit_frame)
        self.AdvancedParameters_Syn1Gain_frame.setObjectName(u"AdvancedParameters_Syn1Gain_frame")
        self.AdvancedParameters_Syn1Gain_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_Syn1Gain_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.AdvancedParameters_Syn1Gain_frame)
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Syn1Gain_label_frame = QFrame(self.AdvancedParameters_Syn1Gain_frame)
        self.AdvancedParameters_Syn1Gain_label_frame.setObjectName(u"AdvancedParameters_Syn1Gain_label_frame")
        self.AdvancedParameters_Syn1Gain_label_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_Syn1Gain_label_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_10 = QVBoxLayout(self.AdvancedParameters_Syn1Gain_label_frame)
        self.verticalLayout_10.setSpacing(0)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Syn1Gain_label = QLabel(self.AdvancedParameters_Syn1Gain_label_frame)
        self.AdvancedParameters_Syn1Gain_label.setObjectName(u"AdvancedParameters_Syn1Gain_label")
        self.AdvancedParameters_Syn1Gain_label.setFont(font1)

        self.verticalLayout_10.addWidget(self.AdvancedParameters_Syn1Gain_label)


        self.horizontalLayout_5.addWidget(self.AdvancedParameters_Syn1Gain_label_frame)

        self.AdvancedParameters_Syn1Gain_lineEdit_frame = QFrame(self.AdvancedParameters_Syn1Gain_frame)
        self.AdvancedParameters_Syn1Gain_lineEdit_frame.setObjectName(u"AdvancedParameters_Syn1Gain_lineEdit_frame")
        self.AdvancedParameters_Syn1Gain_lineEdit_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_Syn1Gain_lineEdit_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_14 = QVBoxLayout(self.AdvancedParameters_Syn1Gain_lineEdit_frame)
        self.verticalLayout_14.setSpacing(0)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.verticalLayout_14.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Syn1Gain_lineEdit = QLineEdit(self.AdvancedParameters_Syn1Gain_lineEdit_frame)
        self.AdvancedParameters_Syn1Gain_lineEdit.setObjectName(u"AdvancedParameters_Syn1Gain_lineEdit")
        self.AdvancedParameters_Syn1Gain_lineEdit.setMaximumSize(QSize(100, 16777215))
        self.AdvancedParameters_Syn1Gain_lineEdit.setFont(font2)
        self.AdvancedParameters_Syn1Gain_lineEdit.setAlignment(Qt.AlignCenter)

        self.verticalLayout_14.addWidget(self.AdvancedParameters_Syn1Gain_lineEdit, 0, Qt.AlignRight)


        self.horizontalLayout_5.addWidget(self.AdvancedParameters_Syn1Gain_lineEdit_frame)


        self.verticalLayout_3.addWidget(self.AdvancedParameters_Syn1Gain_frame)

        self.AdvancedParameters_Syn1Decay_frame = QFrame(self.AdvancedParameters_lineEdit_frame)
        self.AdvancedParameters_Syn1Decay_frame.setObjectName(u"AdvancedParameters_Syn1Decay_frame")
        self.AdvancedParameters_Syn1Decay_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_Syn1Decay_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_6 = QHBoxLayout(self.AdvancedParameters_Syn1Decay_frame)
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Syn1Decay_label_frame = QFrame(self.AdvancedParameters_Syn1Decay_frame)
        self.AdvancedParameters_Syn1Decay_label_frame.setObjectName(u"AdvancedParameters_Syn1Decay_label_frame")
        self.AdvancedParameters_Syn1Decay_label_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_Syn1Decay_label_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_8 = QVBoxLayout(self.AdvancedParameters_Syn1Decay_label_frame)
        self.verticalLayout_8.setSpacing(0)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Syn1Decay_label = QLabel(self.AdvancedParameters_Syn1Decay_label_frame)
        self.AdvancedParameters_Syn1Decay_label.setObjectName(u"AdvancedParameters_Syn1Decay_label")
        self.AdvancedParameters_Syn1Decay_label.setFont(font1)

        self.verticalLayout_8.addWidget(self.AdvancedParameters_Syn1Decay_label)


        self.horizontalLayout_6.addWidget(self.AdvancedParameters_Syn1Decay_label_frame)

        self.AdvancedParameters_Syn1Decay_lineEdit_frame = QFrame(self.AdvancedParameters_Syn1Decay_frame)
        self.AdvancedParameters_Syn1Decay_lineEdit_frame.setObjectName(u"AdvancedParameters_Syn1Decay_lineEdit_frame")
        self.AdvancedParameters_Syn1Decay_lineEdit_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_Syn1Decay_lineEdit_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_15 = QVBoxLayout(self.AdvancedParameters_Syn1Decay_lineEdit_frame)
        self.verticalLayout_15.setSpacing(0)
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.verticalLayout_15.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Syn1Decay_lineEdit = QLineEdit(self.AdvancedParameters_Syn1Decay_lineEdit_frame)
        self.AdvancedParameters_Syn1Decay_lineEdit.setObjectName(u"AdvancedParameters_Syn1Decay_lineEdit")
        self.AdvancedParameters_Syn1Decay_lineEdit.setMaximumSize(QSize(100, 16777215))
        self.AdvancedParameters_Syn1Decay_lineEdit.setFont(font2)
        self.AdvancedParameters_Syn1Decay_lineEdit.setAlignment(Qt.AlignCenter)

        self.verticalLayout_15.addWidget(self.AdvancedParameters_Syn1Decay_lineEdit, 0, Qt.AlignRight)


        self.horizontalLayout_6.addWidget(self.AdvancedParameters_Syn1Decay_lineEdit_frame)


        self.verticalLayout_3.addWidget(self.AdvancedParameters_Syn1Decay_frame)

        self.Space_frame2 = QFrame(self.AdvancedParameters_lineEdit_frame)
        self.Space_frame2.setObjectName(u"Space_frame2")
        self.Space_frame2.setFrameShape(QFrame.StyledPanel)
        self.Space_frame2.setFrameShadow(QFrame.Raised)
        self.verticalLayout_20 = QVBoxLayout(self.Space_frame2)
        self.verticalLayout_20.setObjectName(u"verticalLayout_20")
        self.verticalLayout_20.setContentsMargins(5, 5, 5, 5)

        self.verticalLayout_3.addWidget(self.Space_frame2)

        self.AdvancedParameters_Syn2Gain_frame = QFrame(self.AdvancedParameters_lineEdit_frame)
        self.AdvancedParameters_Syn2Gain_frame.setObjectName(u"AdvancedParameters_Syn2Gain_frame")
        self.AdvancedParameters_Syn2Gain_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_Syn2Gain_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.AdvancedParameters_Syn2Gain_frame)
        self.horizontalLayout_7.setSpacing(0)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Syn2Gain_label_frame = QFrame(self.AdvancedParameters_Syn2Gain_frame)
        self.AdvancedParameters_Syn2Gain_label_frame.setObjectName(u"AdvancedParameters_Syn2Gain_label_frame")
        self.AdvancedParameters_Syn2Gain_label_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_Syn2Gain_label_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_11 = QVBoxLayout(self.AdvancedParameters_Syn2Gain_label_frame)
        self.verticalLayout_11.setSpacing(0)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.verticalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Syn2Gain_label = QLabel(self.AdvancedParameters_Syn2Gain_label_frame)
        self.AdvancedParameters_Syn2Gain_label.setObjectName(u"AdvancedParameters_Syn2Gain_label")
        self.AdvancedParameters_Syn2Gain_label.setFont(font1)

        self.verticalLayout_11.addWidget(self.AdvancedParameters_Syn2Gain_label)


        self.horizontalLayout_7.addWidget(self.AdvancedParameters_Syn2Gain_label_frame)

        self.AdvancedParameters_Syn2Gain_lineEdit_frame = QFrame(self.AdvancedParameters_Syn2Gain_frame)
        self.AdvancedParameters_Syn2Gain_lineEdit_frame.setObjectName(u"AdvancedParameters_Syn2Gain_lineEdit_frame")
        self.AdvancedParameters_Syn2Gain_lineEdit_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_Syn2Gain_lineEdit_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_16 = QVBoxLayout(self.AdvancedParameters_Syn2Gain_lineEdit_frame)
        self.verticalLayout_16.setSpacing(0)
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.verticalLayout_16.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Syn2Gain_lineEdit = QLineEdit(self.AdvancedParameters_Syn2Gain_lineEdit_frame)
        self.AdvancedParameters_Syn2Gain_lineEdit.setObjectName(u"AdvancedParameters_Syn2Gain_lineEdit")
        self.AdvancedParameters_Syn2Gain_lineEdit.setMaximumSize(QSize(100, 16777215))
        self.AdvancedParameters_Syn2Gain_lineEdit.setFont(font2)
        self.AdvancedParameters_Syn2Gain_lineEdit.setAlignment(Qt.AlignCenter)

        self.verticalLayout_16.addWidget(self.AdvancedParameters_Syn2Gain_lineEdit, 0, Qt.AlignRight)


        self.horizontalLayout_7.addWidget(self.AdvancedParameters_Syn2Gain_lineEdit_frame)


        self.verticalLayout_3.addWidget(self.AdvancedParameters_Syn2Gain_frame)

        self.AdvancedParameters_Syn2Decay_frame = QFrame(self.AdvancedParameters_lineEdit_frame)
        self.AdvancedParameters_Syn2Decay_frame.setObjectName(u"AdvancedParameters_Syn2Decay_frame")
        self.AdvancedParameters_Syn2Decay_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_Syn2Decay_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_9 = QHBoxLayout(self.AdvancedParameters_Syn2Decay_frame)
        self.horizontalLayout_9.setSpacing(0)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Syn2Decay_label_frame = QFrame(self.AdvancedParameters_Syn2Decay_frame)
        self.AdvancedParameters_Syn2Decay_label_frame.setObjectName(u"AdvancedParameters_Syn2Decay_label_frame")
        self.AdvancedParameters_Syn2Decay_label_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_Syn2Decay_label_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_9 = QVBoxLayout(self.AdvancedParameters_Syn2Decay_label_frame)
        self.verticalLayout_9.setSpacing(0)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Syn2Decay_label = QLabel(self.AdvancedParameters_Syn2Decay_label_frame)
        self.AdvancedParameters_Syn2Decay_label.setObjectName(u"AdvancedParameters_Syn2Decay_label")
        self.AdvancedParameters_Syn2Decay_label.setFont(font1)

        self.verticalLayout_9.addWidget(self.AdvancedParameters_Syn2Decay_label)


        self.horizontalLayout_9.addWidget(self.AdvancedParameters_Syn2Decay_label_frame)

        self.AdvancedParameters_Syn2Decay_lineEdit_frame = QFrame(self.AdvancedParameters_Syn2Decay_frame)
        self.AdvancedParameters_Syn2Decay_lineEdit_frame.setObjectName(u"AdvancedParameters_Syn2Decay_lineEdit_frame")
        self.AdvancedParameters_Syn2Decay_lineEdit_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_Syn2Decay_lineEdit_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_17 = QVBoxLayout(self.AdvancedParameters_Syn2Decay_lineEdit_frame)
        self.verticalLayout_17.setSpacing(0)
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.verticalLayout_17.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Syn2Decay_lineEdit = QLineEdit(self.AdvancedParameters_Syn2Decay_lineEdit_frame)
        self.AdvancedParameters_Syn2Decay_lineEdit.setObjectName(u"AdvancedParameters_Syn2Decay_lineEdit")
        self.AdvancedParameters_Syn2Decay_lineEdit.setMaximumSize(QSize(100, 16777215))
        self.AdvancedParameters_Syn2Decay_lineEdit.setFont(font2)
        self.AdvancedParameters_Syn2Decay_lineEdit.setAlignment(Qt.AlignCenter)

        self.verticalLayout_17.addWidget(self.AdvancedParameters_Syn2Decay_lineEdit, 0, Qt.AlignRight)


        self.horizontalLayout_9.addWidget(self.AdvancedParameters_Syn2Decay_lineEdit_frame)


        self.verticalLayout_3.addWidget(self.AdvancedParameters_Syn2Decay_frame)


        self.verticalLayout_2.addWidget(self.AdvancedParameters_lineEdit_frame)

        self.AdvancedParameters_Button_frame = QFrame(self.AdvancedParameters_frame)
        self.AdvancedParameters_Button_frame.setObjectName(u"AdvancedParameters_Button_frame")
        self.AdvancedParameters_Button_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_Button_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_10 = QHBoxLayout(self.AdvancedParameters_Button_frame)
        self.horizontalLayout_10.setSpacing(0)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Button_Save_frame = QFrame(self.AdvancedParameters_Button_frame)
        self.AdvancedParameters_Button_Save_frame.setObjectName(u"AdvancedParameters_Button_Save_frame")
        self.AdvancedParameters_Button_Save_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_Button_Save_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_19 = QVBoxLayout(self.AdvancedParameters_Button_Save_frame)
        self.verticalLayout_19.setSpacing(0)
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.verticalLayout_19.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Button_Save_pushButton = QPushButton(self.AdvancedParameters_Button_Save_frame)
        self.AdvancedParameters_Button_Save_pushButton.setObjectName(u"AdvancedParameters_Button_Save_pushButton")
        self.AdvancedParameters_Button_Save_pushButton.setFont(font2)

        self.verticalLayout_19.addWidget(self.AdvancedParameters_Button_Save_pushButton, 0, Qt.AlignHCenter)


        self.horizontalLayout_10.addWidget(self.AdvancedParameters_Button_Save_frame)

        self.AdvancedParameters_Button_Exit_frame = QFrame(self.AdvancedParameters_Button_frame)
        self.AdvancedParameters_Button_Exit_frame.setObjectName(u"AdvancedParameters_Button_Exit_frame")
        self.AdvancedParameters_Button_Exit_frame.setFrameShape(QFrame.StyledPanel)
        self.AdvancedParameters_Button_Exit_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_18 = QVBoxLayout(self.AdvancedParameters_Button_Exit_frame)
        self.verticalLayout_18.setSpacing(0)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.verticalLayout_18.setContentsMargins(0, 0, 0, 0)
        self.AdvancedParameters_Button_Exit_pushButton = QPushButton(self.AdvancedParameters_Button_Exit_frame)
        self.AdvancedParameters_Button_Exit_pushButton.setObjectName(u"AdvancedParameters_Button_Exit_pushButton")
        self.AdvancedParameters_Button_Exit_pushButton.setFont(font2)

        self.verticalLayout_18.addWidget(self.AdvancedParameters_Button_Exit_pushButton, 0, Qt.AlignHCenter)


        self.horizontalLayout_10.addWidget(self.AdvancedParameters_Button_Exit_frame)


        self.verticalLayout_2.addWidget(self.AdvancedParameters_Button_frame)


        self.horizontalLayout.addWidget(self.AdvancedParameters_frame)

        AdvancedParameters.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(AdvancedParameters)
        self.statusbar.setObjectName(u"statusbar")
        AdvancedParameters.setStatusBar(self.statusbar)

        self.retranslateUi(AdvancedParameters)

        QMetaObject.connectSlotsByName(AdvancedParameters)
    # setupUi

    def retranslateUi(self, AdvancedParameters):
        AdvancedParameters.setWindowTitle(QCoreApplication.translate("AdvancedParameters", u"MainWindow", None))
        self.AdvancedParameters_Title_label.setText(QCoreApplication.translate("AdvancedParameters", u"Neuron Advanced Parameters", None))
        self.AdvancedParameters_PRGain_label.setText(QCoreApplication.translate("AdvancedParameters", u"Photo-Receptor Gain (%)", None))
        self.AdvancedParameters_PRGain_lineEdit.setText(QCoreApplication.translate("AdvancedParameters", u"0", None))
        self.AdvancedParameters_PRDecay_label.setText(QCoreApplication.translate("AdvancedParameters", u"Photo-Receptor Decay (ms\u05bf \u00b9)", None))
        self.AdvancedParameters_PRDecay_lineEdit.setText(QCoreApplication.translate("AdvancedParameters", u"0.001", None))
        self.AdvancedParameters_PRRecovery_label.setText(QCoreApplication.translate("AdvancedParameters", u"Photo-Receptor Recovery (ms\u05bf \u00b9)", None))
        self.AdvancedParameters_PRRecovery_lineEdit.setText(QCoreApplication.translate("AdvancedParameters", u"0.025", None))
        self.AdvancedParameters_Syn1Gain_label.setText(QCoreApplication.translate("AdvancedParameters", u"Synapse 1 Gain (%)", None))
        self.AdvancedParameters_Syn1Gain_lineEdit.setText(QCoreApplication.translate("AdvancedParameters", u"0", None))
        self.AdvancedParameters_Syn1Decay_label.setText(QCoreApplication.translate("AdvancedParameters", u"Synapse 1 Decay (ms\u05bf \u00b9) ", None))
        self.AdvancedParameters_Syn1Decay_lineEdit.setText(QCoreApplication.translate("AdvancedParameters", u"0.995", None))
        self.AdvancedParameters_Syn2Gain_label.setText(QCoreApplication.translate("AdvancedParameters", u"Synapse 2 Gain (%)", None))
        self.AdvancedParameters_Syn2Gain_lineEdit.setText(QCoreApplication.translate("AdvancedParameters", u"0", None))
        self.AdvancedParameters_Syn2Decay_label.setText(QCoreApplication.translate("AdvancedParameters", u"Synapse 2 Decay (ms\u05bf \u00b9) ", None))
        self.AdvancedParameters_Syn2Decay_lineEdit.setText(QCoreApplication.translate("AdvancedParameters", u"0.995", None))
        self.AdvancedParameters_Button_Save_pushButton.setText(QCoreApplication.translate("AdvancedParameters", u"  Save Parameters  ", None))
        self.AdvancedParameters_Button_Exit_pushButton.setText(QCoreApplication.translate("AdvancedParameters", u"  Exit without saving  ", None))
    # retranslateUi

