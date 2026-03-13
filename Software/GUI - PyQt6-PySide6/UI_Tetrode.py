# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'UI_Tetrode.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QDoubleSpinBox,
    QFrame, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QSizePolicy, QSpinBox,
    QVBoxLayout, QWidget)

from geometry_view import GeometryView
import resources_rc

class Ui_Tetrode(object):
    def setupUi(self, Tetrode):
        if not Tetrode.objectName():
            Tetrode.setObjectName(u"Tetrode")
        Tetrode.resize(1096, 626)
        Tetrode.setStyleSheet(u"*{\n"
"	border:none;\n"
"	background-color: transparent;\n"
"	background: transparent;\n"
"	padding: 0;\n"
"	margin:0;\n"
"	color: rgb(190, 205, 205);    \n"
"}\n"
"#Tetrode_Main_frame {\n"
"	background-color: rgb(0, 30, 38);\n"
"	border-radius: 25px;\n"
"    border: 1px solid rgb(190, 205, 205);\n"
"}\n"
"\n"
"QDoubleSpinBox{\n"
"	border: 1px solid rgb(190, 205, 205);\n"
"	background-color: rgb(7, 54, 66);\n"
"	padding: 2px;\n"
"}\n"
"QSpinBox{\n"
"	border: 1px solid rgb(190, 205, 205);\n"
"	background-color: rgb(7, 54, 66);\n"
"	padding: 2px;\n"
"}\n"
"QPushButton{\n"
"	padding: 10px 5px;\n"
"	border-radius:15px;\n"
"	background-color: rgb(7, 54, 66);\n"
"}\n"
" QPushButton:hover{\n"
"	background-color: rgb(0, 30, 38);\n"
"}\n"
"\n"
"\n"
"#Tetrode_graphicsView {\n"
"	background-color: rgb(0, 43, 54);\n"
"}\n"
"")
        self.centralwidget = QWidget(Tetrode)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_9 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_9.setSpacing(0)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Main_frame = QFrame(self.centralwidget)
        self.Tetrode_Main_frame.setObjectName(u"Tetrode_Main_frame")
        self.Tetrode_Main_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Main_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.Tetrode_Main_frame)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Header_widget = QWidget(self.Tetrode_Main_frame)
        self.Tetrode_Header_widget.setObjectName(u"Tetrode_Header_widget")
        self.horizontalLayout_10 = QHBoxLayout(self.Tetrode_Header_widget)
        self.horizontalLayout_10.setSpacing(0)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(0, 10, 0, 10)
        self.Tetrode_Header_empty_frame = QFrame(self.Tetrode_Header_widget)
        self.Tetrode_Header_empty_frame.setObjectName(u"Tetrode_Header_empty_frame")
        self.Tetrode_Header_empty_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Header_empty_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.Tetrode_Header_empty_frame)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)

        self.horizontalLayout_10.addWidget(self.Tetrode_Header_empty_frame)

        self.Tetrode_Header_label_frame = QFrame(self.Tetrode_Header_widget)
        self.Tetrode_Header_label_frame.setObjectName(u"Tetrode_Header_label_frame")
        self.Tetrode_Header_label_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Header_label_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_23 = QVBoxLayout(self.Tetrode_Header_label_frame)
        self.verticalLayout_23.setObjectName(u"verticalLayout_23")
        self.verticalLayout_23.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Header_label = QLabel(self.Tetrode_Header_label_frame)
        self.Tetrode_Header_label.setObjectName(u"Tetrode_Header_label")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.Tetrode_Header_label.setFont(font)
        self.Tetrode_Header_label.setStyleSheet(u"color: rgb(190, 205, 205);")

        self.verticalLayout_23.addWidget(self.Tetrode_Header_label)


        self.horizontalLayout_10.addWidget(self.Tetrode_Header_label_frame, 0, Qt.AlignHCenter)

        self.Tetrode_Close_pushButton_frame = QFrame(self.Tetrode_Header_widget)
        self.Tetrode_Close_pushButton_frame.setObjectName(u"Tetrode_Close_pushButton_frame")
        self.Tetrode_Close_pushButton_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Close_pushButton_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_15 = QHBoxLayout(self.Tetrode_Close_pushButton_frame)
        self.horizontalLayout_15.setSpacing(0)
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.horizontalLayout_15.setContentsMargins(0, 0, 10, 0)
        self.Tetrode_Close_pushButton = QPushButton(self.Tetrode_Close_pushButton_frame)
        self.Tetrode_Close_pushButton.setObjectName(u"Tetrode_Close_pushButton")
        self.Tetrode_Close_pushButton.setMinimumSize(QSize(30, 30))
        self.Tetrode_Close_pushButton.setMaximumSize(QSize(30, 16777215))
        self.Tetrode_Close_pushButton.setStyleSheet(u"background-color: rgb(0, 30, 38);")
        icon = QIcon()
        icon.addFile(u":/resources/resources/Exit.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.Tetrode_Close_pushButton.setIcon(icon)
        self.Tetrode_Close_pushButton.setIconSize(QSize(24, 24))

        self.horizontalLayout_15.addWidget(self.Tetrode_Close_pushButton)


        self.horizontalLayout_10.addWidget(self.Tetrode_Close_pushButton_frame, 0, Qt.AlignRight)


        self.verticalLayout_3.addWidget(self.Tetrode_Header_widget)

        self.Tetrode_Center_frame = QFrame(self.Tetrode_Main_frame)
        self.Tetrode_Center_frame.setObjectName(u"Tetrode_Center_frame")
        self.Tetrode_Center_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Center_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.Tetrode_Center_frame)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_frame = QFrame(self.Tetrode_Center_frame)
        self.Tetrode_Parameters_frame.setObjectName(u"Tetrode_Parameters_frame")
        self.Tetrode_Parameters_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.Tetrode_Parameters_frame)
        self.verticalLayout_5.setSpacing(10)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.line_4 = QFrame(self.Tetrode_Parameters_frame)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setStyleSheet(u"background-color: rgb(0, 43, 54);")
        self.line_4.setFrameShape(QFrame.Shape.HLine)
        self.line_4.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_5.addWidget(self.line_4)

        self.Tetrode_Parameters_Neurons_groupBox = QGroupBox(self.Tetrode_Parameters_frame)
        self.Tetrode_Parameters_Neurons_groupBox.setObjectName(u"Tetrode_Parameters_Neurons_groupBox")
        self.verticalLayout_2 = QVBoxLayout(self.Tetrode_Parameters_Neurons_groupBox)
        self.verticalLayout_2.setSpacing(20)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(10, 0, 10, 0)
        self.Tetrode_Parameters_Spikeling1_frame = QFrame(self.Tetrode_Parameters_Neurons_groupBox)
        self.Tetrode_Parameters_Spikeling1_frame.setObjectName(u"Tetrode_Parameters_Spikeling1_frame")
        self.Tetrode_Parameters_Spikeling1_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Spikeling1_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_7 = QVBoxLayout(self.Tetrode_Parameters_Spikeling1_frame)
        self.verticalLayout_7.setSpacing(5)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_Spikeling1_label_frame = QFrame(self.Tetrode_Parameters_Spikeling1_frame)
        self.Tetrode_Parameters_Spikeling1_label_frame.setObjectName(u"Tetrode_Parameters_Spikeling1_label_frame")
        self.Tetrode_Parameters_Spikeling1_label_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Spikeling1_label_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_12 = QVBoxLayout(self.Tetrode_Parameters_Spikeling1_label_frame)
        self.verticalLayout_12.setSpacing(0)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalLayout_12.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_Spikeling1_label = QLabel(self.Tetrode_Parameters_Spikeling1_label_frame)
        self.Tetrode_Parameters_Spikeling1_label.setObjectName(u"Tetrode_Parameters_Spikeling1_label")
        font1 = QFont()
        font1.setPointSize(12)
        font1.setBold(True)
        self.Tetrode_Parameters_Spikeling1_label.setFont(font1)

        self.verticalLayout_12.addWidget(self.Tetrode_Parameters_Spikeling1_label)


        self.verticalLayout_7.addWidget(self.Tetrode_Parameters_Spikeling1_label_frame)

        self.Tetrode_Parameters_Spikeling1_Coordinate_frame = QFrame(self.Tetrode_Parameters_Spikeling1_frame)
        self.Tetrode_Parameters_Spikeling1_Coordinate_frame.setObjectName(u"Tetrode_Parameters_Spikeling1_Coordinate_frame")
        self.Tetrode_Parameters_Spikeling1_Coordinate_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Spikeling1_Coordinate_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.Tetrode_Parameters_Spikeling1_Coordinate_frame)
        self.horizontalLayout_2.setSpacing(5)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_Spikeling1_x_label = QLabel(self.Tetrode_Parameters_Spikeling1_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling1_x_label.setObjectName(u"Tetrode_Parameters_Spikeling1_x_label")

        self.horizontalLayout_2.addWidget(self.Tetrode_Parameters_Spikeling1_x_label, 0, Qt.AlignHCenter)

        self.Tetrode_Parameters_Spikeling1_x_doubleSpinBox = QDoubleSpinBox(self.Tetrode_Parameters_Spikeling1_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling1_x_doubleSpinBox.setObjectName(u"Tetrode_Parameters_Spikeling1_x_doubleSpinBox")
        self.Tetrode_Parameters_Spikeling1_x_doubleSpinBox.setDecimals(1)
        self.Tetrode_Parameters_Spikeling1_x_doubleSpinBox.setMinimum(-500.000000000000000)
        self.Tetrode_Parameters_Spikeling1_x_doubleSpinBox.setMaximum(500.000000000000000)
        self.Tetrode_Parameters_Spikeling1_x_doubleSpinBox.setValue(0.000000000000000)

        self.horizontalLayout_2.addWidget(self.Tetrode_Parameters_Spikeling1_x_doubleSpinBox)

        self.Tetrode_Parameters_Spikeling1_y_label = QLabel(self.Tetrode_Parameters_Spikeling1_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling1_y_label.setObjectName(u"Tetrode_Parameters_Spikeling1_y_label")

        self.horizontalLayout_2.addWidget(self.Tetrode_Parameters_Spikeling1_y_label, 0, Qt.AlignHCenter)

        self.Tetrode_Parameters_Spikeling1_y_doubleSpinBox = QDoubleSpinBox(self.Tetrode_Parameters_Spikeling1_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling1_y_doubleSpinBox.setObjectName(u"Tetrode_Parameters_Spikeling1_y_doubleSpinBox")
        self.Tetrode_Parameters_Spikeling1_y_doubleSpinBox.setDecimals(1)
        self.Tetrode_Parameters_Spikeling1_y_doubleSpinBox.setMinimum(-500.000000000000000)
        self.Tetrode_Parameters_Spikeling1_y_doubleSpinBox.setMaximum(500.000000000000000)

        self.horizontalLayout_2.addWidget(self.Tetrode_Parameters_Spikeling1_y_doubleSpinBox)

        self.Tetrode_Parameters_Spikeling1_z_label = QLabel(self.Tetrode_Parameters_Spikeling1_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling1_z_label.setObjectName(u"Tetrode_Parameters_Spikeling1_z_label")

        self.horizontalLayout_2.addWidget(self.Tetrode_Parameters_Spikeling1_z_label, 0, Qt.AlignHCenter)

        self.Tetrode_Parameters_Spikeling1_z_doubleSpinBox = QDoubleSpinBox(self.Tetrode_Parameters_Spikeling1_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling1_z_doubleSpinBox.setObjectName(u"Tetrode_Parameters_Spikeling1_z_doubleSpinBox")
        self.Tetrode_Parameters_Spikeling1_z_doubleSpinBox.setDecimals(1)
        self.Tetrode_Parameters_Spikeling1_z_doubleSpinBox.setMinimum(-500.000000000000000)
        self.Tetrode_Parameters_Spikeling1_z_doubleSpinBox.setMaximum(500.000000000000000)

        self.horizontalLayout_2.addWidget(self.Tetrode_Parameters_Spikeling1_z_doubleSpinBox)


        self.verticalLayout_7.addWidget(self.Tetrode_Parameters_Spikeling1_Coordinate_frame)


        self.verticalLayout_2.addWidget(self.Tetrode_Parameters_Spikeling1_frame)

        self.Tetrode_Parameters_Spikeling2_frame = QFrame(self.Tetrode_Parameters_Neurons_groupBox)
        self.Tetrode_Parameters_Spikeling2_frame.setObjectName(u"Tetrode_Parameters_Spikeling2_frame")
        self.Tetrode_Parameters_Spikeling2_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Spikeling2_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_8 = QVBoxLayout(self.Tetrode_Parameters_Spikeling2_frame)
        self.verticalLayout_8.setSpacing(5)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_Spikeling2_label_frame = QFrame(self.Tetrode_Parameters_Spikeling2_frame)
        self.Tetrode_Parameters_Spikeling2_label_frame.setObjectName(u"Tetrode_Parameters_Spikeling2_label_frame")
        self.Tetrode_Parameters_Spikeling2_label_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Spikeling2_label_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_11 = QVBoxLayout(self.Tetrode_Parameters_Spikeling2_label_frame)
        self.verticalLayout_11.setSpacing(0)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.verticalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_Spikeling2_label = QLabel(self.Tetrode_Parameters_Spikeling2_label_frame)
        self.Tetrode_Parameters_Spikeling2_label.setObjectName(u"Tetrode_Parameters_Spikeling2_label")
        self.Tetrode_Parameters_Spikeling2_label.setFont(font1)

        self.verticalLayout_11.addWidget(self.Tetrode_Parameters_Spikeling2_label)


        self.verticalLayout_8.addWidget(self.Tetrode_Parameters_Spikeling2_label_frame)

        self.Tetrode_Parameters_Spikeling2_Coordinate_frame = QFrame(self.Tetrode_Parameters_Spikeling2_frame)
        self.Tetrode_Parameters_Spikeling2_Coordinate_frame.setObjectName(u"Tetrode_Parameters_Spikeling2_Coordinate_frame")
        self.Tetrode_Parameters_Spikeling2_Coordinate_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Spikeling2_Coordinate_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.Tetrode_Parameters_Spikeling2_Coordinate_frame)
        self.horizontalLayout_4.setSpacing(5)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_Spikeling2_x_label = QLabel(self.Tetrode_Parameters_Spikeling2_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling2_x_label.setObjectName(u"Tetrode_Parameters_Spikeling2_x_label")

        self.horizontalLayout_4.addWidget(self.Tetrode_Parameters_Spikeling2_x_label, 0, Qt.AlignHCenter)

        self.Tetrode_Parameters_Spikeling2_x_doubleSpinBox = QDoubleSpinBox(self.Tetrode_Parameters_Spikeling2_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling2_x_doubleSpinBox.setObjectName(u"Tetrode_Parameters_Spikeling2_x_doubleSpinBox")
        self.Tetrode_Parameters_Spikeling2_x_doubleSpinBox.setDecimals(1)
        self.Tetrode_Parameters_Spikeling2_x_doubleSpinBox.setMinimum(-500.000000000000000)
        self.Tetrode_Parameters_Spikeling2_x_doubleSpinBox.setMaximum(500.000000000000000)
        self.Tetrode_Parameters_Spikeling2_x_doubleSpinBox.setValue(-40.000000000000000)

        self.horizontalLayout_4.addWidget(self.Tetrode_Parameters_Spikeling2_x_doubleSpinBox)

        self.Tetrode_Parameters_Spikeling2_y_label = QLabel(self.Tetrode_Parameters_Spikeling2_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling2_y_label.setObjectName(u"Tetrode_Parameters_Spikeling2_y_label")

        self.horizontalLayout_4.addWidget(self.Tetrode_Parameters_Spikeling2_y_label, 0, Qt.AlignHCenter)

        self.Tetrode_Parameters_Spikeling2_y_doubleSpinBox = QDoubleSpinBox(self.Tetrode_Parameters_Spikeling2_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling2_y_doubleSpinBox.setObjectName(u"Tetrode_Parameters_Spikeling2_y_doubleSpinBox")
        self.Tetrode_Parameters_Spikeling2_y_doubleSpinBox.setDecimals(1)
        self.Tetrode_Parameters_Spikeling2_y_doubleSpinBox.setMinimum(-500.000000000000000)
        self.Tetrode_Parameters_Spikeling2_y_doubleSpinBox.setMaximum(500.000000000000000)
        self.Tetrode_Parameters_Spikeling2_y_doubleSpinBox.setValue(15.000000000000000)

        self.horizontalLayout_4.addWidget(self.Tetrode_Parameters_Spikeling2_y_doubleSpinBox)

        self.Tetrode_Parameters_Spikeling2_z_label = QLabel(self.Tetrode_Parameters_Spikeling2_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling2_z_label.setObjectName(u"Tetrode_Parameters_Spikeling2_z_label")

        self.horizontalLayout_4.addWidget(self.Tetrode_Parameters_Spikeling2_z_label, 0, Qt.AlignHCenter)

        self.Tetrode_Parameters_Spikeling2_z_doubleSpinBox = QDoubleSpinBox(self.Tetrode_Parameters_Spikeling2_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling2_z_doubleSpinBox.setObjectName(u"Tetrode_Parameters_Spikeling2_z_doubleSpinBox")
        self.Tetrode_Parameters_Spikeling2_z_doubleSpinBox.setDecimals(1)
        self.Tetrode_Parameters_Spikeling2_z_doubleSpinBox.setMinimum(-500.000000000000000)
        self.Tetrode_Parameters_Spikeling2_z_doubleSpinBox.setMaximum(500.000000000000000)

        self.horizontalLayout_4.addWidget(self.Tetrode_Parameters_Spikeling2_z_doubleSpinBox)


        self.verticalLayout_8.addWidget(self.Tetrode_Parameters_Spikeling2_Coordinate_frame)


        self.verticalLayout_2.addWidget(self.Tetrode_Parameters_Spikeling2_frame)

        self.Tetrode_Parameters_Spikeling3_frame = QFrame(self.Tetrode_Parameters_Neurons_groupBox)
        self.Tetrode_Parameters_Spikeling3_frame.setObjectName(u"Tetrode_Parameters_Spikeling3_frame")
        self.Tetrode_Parameters_Spikeling3_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Spikeling3_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_9 = QVBoxLayout(self.Tetrode_Parameters_Spikeling3_frame)
        self.verticalLayout_9.setSpacing(5)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_Spikeling3_label_frame = QFrame(self.Tetrode_Parameters_Spikeling3_frame)
        self.Tetrode_Parameters_Spikeling3_label_frame.setObjectName(u"Tetrode_Parameters_Spikeling3_label_frame")
        self.Tetrode_Parameters_Spikeling3_label_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Spikeling3_label_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_10 = QVBoxLayout(self.Tetrode_Parameters_Spikeling3_label_frame)
        self.verticalLayout_10.setSpacing(0)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_Spikeling3_label = QLabel(self.Tetrode_Parameters_Spikeling3_label_frame)
        self.Tetrode_Parameters_Spikeling3_label.setObjectName(u"Tetrode_Parameters_Spikeling3_label")
        self.Tetrode_Parameters_Spikeling3_label.setFont(font1)

        self.verticalLayout_10.addWidget(self.Tetrode_Parameters_Spikeling3_label)


        self.verticalLayout_9.addWidget(self.Tetrode_Parameters_Spikeling3_label_frame)

        self.Tetrode_Parameters_Spikeling3_Coordinate_frame = QFrame(self.Tetrode_Parameters_Spikeling3_frame)
        self.Tetrode_Parameters_Spikeling3_Coordinate_frame.setObjectName(u"Tetrode_Parameters_Spikeling3_Coordinate_frame")
        self.Tetrode_Parameters_Spikeling3_Coordinate_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Spikeling3_Coordinate_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.Tetrode_Parameters_Spikeling3_Coordinate_frame)
        self.horizontalLayout_3.setSpacing(5)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_Spikeling3_x_label = QLabel(self.Tetrode_Parameters_Spikeling3_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling3_x_label.setObjectName(u"Tetrode_Parameters_Spikeling3_x_label")

        self.horizontalLayout_3.addWidget(self.Tetrode_Parameters_Spikeling3_x_label, 0, Qt.AlignHCenter)

        self.Tetrode_Parameters_Spikeling3_x_doubleSpinBox = QDoubleSpinBox(self.Tetrode_Parameters_Spikeling3_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling3_x_doubleSpinBox.setObjectName(u"Tetrode_Parameters_Spikeling3_x_doubleSpinBox")
        self.Tetrode_Parameters_Spikeling3_x_doubleSpinBox.setDecimals(1)
        self.Tetrode_Parameters_Spikeling3_x_doubleSpinBox.setMinimum(-500.000000000000000)
        self.Tetrode_Parameters_Spikeling3_x_doubleSpinBox.setMaximum(500.000000000000000)
        self.Tetrode_Parameters_Spikeling3_x_doubleSpinBox.setValue(-30.000000000000000)

        self.horizontalLayout_3.addWidget(self.Tetrode_Parameters_Spikeling3_x_doubleSpinBox)

        self.Tetrode_Parameters_Spikeling3_y_label = QLabel(self.Tetrode_Parameters_Spikeling3_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling3_y_label.setObjectName(u"Tetrode_Parameters_Spikeling3_y_label")

        self.horizontalLayout_3.addWidget(self.Tetrode_Parameters_Spikeling3_y_label, 0, Qt.AlignHCenter)

        self.Tetrode_Parameters_Spikeling3_y_doubleSpinBox = QDoubleSpinBox(self.Tetrode_Parameters_Spikeling3_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling3_y_doubleSpinBox.setObjectName(u"Tetrode_Parameters_Spikeling3_y_doubleSpinBox")
        self.Tetrode_Parameters_Spikeling3_y_doubleSpinBox.setDecimals(1)
        self.Tetrode_Parameters_Spikeling3_y_doubleSpinBox.setMinimum(-500.000000000000000)
        self.Tetrode_Parameters_Spikeling3_y_doubleSpinBox.setMaximum(500.000000000000000)
        self.Tetrode_Parameters_Spikeling3_y_doubleSpinBox.setValue(-15.000000000000000)

        self.horizontalLayout_3.addWidget(self.Tetrode_Parameters_Spikeling3_y_doubleSpinBox)

        self.Tetrode_Parameters_Spikeling3_z_label = QLabel(self.Tetrode_Parameters_Spikeling3_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling3_z_label.setObjectName(u"Tetrode_Parameters_Spikeling3_z_label")

        self.horizontalLayout_3.addWidget(self.Tetrode_Parameters_Spikeling3_z_label, 0, Qt.AlignHCenter)

        self.Tetrode_Parameters_Spikeling3_z_doubleSpinBox = QDoubleSpinBox(self.Tetrode_Parameters_Spikeling3_Coordinate_frame)
        self.Tetrode_Parameters_Spikeling3_z_doubleSpinBox.setObjectName(u"Tetrode_Parameters_Spikeling3_z_doubleSpinBox")
        self.Tetrode_Parameters_Spikeling3_z_doubleSpinBox.setDecimals(1)
        self.Tetrode_Parameters_Spikeling3_z_doubleSpinBox.setMinimum(-500.000000000000000)
        self.Tetrode_Parameters_Spikeling3_z_doubleSpinBox.setMaximum(500.000000000000000)

        self.horizontalLayout_3.addWidget(self.Tetrode_Parameters_Spikeling3_z_doubleSpinBox)


        self.verticalLayout_9.addWidget(self.Tetrode_Parameters_Spikeling3_Coordinate_frame)


        self.verticalLayout_2.addWidget(self.Tetrode_Parameters_Spikeling3_frame)


        self.verticalLayout_5.addWidget(self.Tetrode_Parameters_Neurons_groupBox)

        self.line = QFrame(self.Tetrode_Parameters_frame)
        self.line.setObjectName(u"line")
        self.line.setStyleSheet(u"background-color: rgb(0, 43, 54);")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_5.addWidget(self.line)

        self.Tetrode_Parameters_Electrode_groupBox = QGroupBox(self.Tetrode_Parameters_frame)
        self.Tetrode_Parameters_Electrode_groupBox.setObjectName(u"Tetrode_Parameters_Electrode_groupBox")
        self.verticalLayout_13 = QVBoxLayout(self.Tetrode_Parameters_Electrode_groupBox)
        self.verticalLayout_13.setSpacing(5)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.verticalLayout_13.setContentsMargins(10, 0, 10, 0)
        self.Tetrode_Parameters_Electrode_label_frame = QFrame(self.Tetrode_Parameters_Electrode_groupBox)
        self.Tetrode_Parameters_Electrode_label_frame.setObjectName(u"Tetrode_Parameters_Electrode_label_frame")
        self.Tetrode_Parameters_Electrode_label_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Electrode_label_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_14 = QVBoxLayout(self.Tetrode_Parameters_Electrode_label_frame)
        self.verticalLayout_14.setSpacing(0)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.verticalLayout_14.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_Electrode_label = QLabel(self.Tetrode_Parameters_Electrode_label_frame)
        self.Tetrode_Parameters_Electrode_label.setObjectName(u"Tetrode_Parameters_Electrode_label")
        self.Tetrode_Parameters_Electrode_label.setFont(font1)

        self.verticalLayout_14.addWidget(self.Tetrode_Parameters_Electrode_label)


        self.verticalLayout_13.addWidget(self.Tetrode_Parameters_Electrode_label_frame)

        self.Tetrode_Parameters_Electrode_Coordinate_frame = QFrame(self.Tetrode_Parameters_Electrode_groupBox)
        self.Tetrode_Parameters_Electrode_Coordinate_frame.setObjectName(u"Tetrode_Parameters_Electrode_Coordinate_frame")
        self.Tetrode_Parameters_Electrode_Coordinate_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Electrode_Coordinate_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.Tetrode_Parameters_Electrode_Coordinate_frame)
        self.horizontalLayout_5.setSpacing(5)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_Electrode_x_label = QLabel(self.Tetrode_Parameters_Electrode_Coordinate_frame)
        self.Tetrode_Parameters_Electrode_x_label.setObjectName(u"Tetrode_Parameters_Electrode_x_label")

        self.horizontalLayout_5.addWidget(self.Tetrode_Parameters_Electrode_x_label, 0, Qt.AlignHCenter)

        self.Tetrode_Parameters_Electrode_x_doubleSpinBox = QDoubleSpinBox(self.Tetrode_Parameters_Electrode_Coordinate_frame)
        self.Tetrode_Parameters_Electrode_x_doubleSpinBox.setObjectName(u"Tetrode_Parameters_Electrode_x_doubleSpinBox")
        self.Tetrode_Parameters_Electrode_x_doubleSpinBox.setDecimals(1)
        self.Tetrode_Parameters_Electrode_x_doubleSpinBox.setMinimum(-500.000000000000000)
        self.Tetrode_Parameters_Electrode_x_doubleSpinBox.setMaximum(500.000000000000000)

        self.horizontalLayout_5.addWidget(self.Tetrode_Parameters_Electrode_x_doubleSpinBox)

        self.Tetrode_Parameters_Electrode_y_label = QLabel(self.Tetrode_Parameters_Electrode_Coordinate_frame)
        self.Tetrode_Parameters_Electrode_y_label.setObjectName(u"Tetrode_Parameters_Electrode_y_label")

        self.horizontalLayout_5.addWidget(self.Tetrode_Parameters_Electrode_y_label, 0, Qt.AlignHCenter)

        self.Tetrode_Parameters_Electrode_y_doubleSpinBox = QDoubleSpinBox(self.Tetrode_Parameters_Electrode_Coordinate_frame)
        self.Tetrode_Parameters_Electrode_y_doubleSpinBox.setObjectName(u"Tetrode_Parameters_Electrode_y_doubleSpinBox")
        self.Tetrode_Parameters_Electrode_y_doubleSpinBox.setDecimals(1)
        self.Tetrode_Parameters_Electrode_y_doubleSpinBox.setMinimum(-500.000000000000000)
        self.Tetrode_Parameters_Electrode_y_doubleSpinBox.setMaximum(500.000000000000000)

        self.horizontalLayout_5.addWidget(self.Tetrode_Parameters_Electrode_y_doubleSpinBox)

        self.Tetrode_Parameters_Electrode_z_label = QLabel(self.Tetrode_Parameters_Electrode_Coordinate_frame)
        self.Tetrode_Parameters_Electrode_z_label.setObjectName(u"Tetrode_Parameters_Electrode_z_label")

        self.horizontalLayout_5.addWidget(self.Tetrode_Parameters_Electrode_z_label, 0, Qt.AlignHCenter)

        self.Tetrode_Parameters_Electrode_z_doubleSpinBox = QDoubleSpinBox(self.Tetrode_Parameters_Electrode_Coordinate_frame)
        self.Tetrode_Parameters_Electrode_z_doubleSpinBox.setObjectName(u"Tetrode_Parameters_Electrode_z_doubleSpinBox")
        self.Tetrode_Parameters_Electrode_z_doubleSpinBox.setDecimals(1)
        self.Tetrode_Parameters_Electrode_z_doubleSpinBox.setMinimum(-500.000000000000000)
        self.Tetrode_Parameters_Electrode_z_doubleSpinBox.setMaximum(500.000000000000000)
        self.Tetrode_Parameters_Electrode_z_doubleSpinBox.setValue(50.000000000000000)

        self.horizontalLayout_5.addWidget(self.Tetrode_Parameters_Electrode_z_doubleSpinBox)


        self.verticalLayout_13.addWidget(self.Tetrode_Parameters_Electrode_Coordinate_frame)

        self.Tetrode_Parameters_Electrode_Position_frame = QFrame(self.Tetrode_Parameters_Electrode_groupBox)
        self.Tetrode_Parameters_Electrode_Position_frame.setObjectName(u"Tetrode_Parameters_Electrode_Position_frame")
        self.Tetrode_Parameters_Electrode_Position_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Electrode_Position_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.Tetrode_Parameters_Electrode_Position_frame)
        self.horizontalLayout_7.setSpacing(20)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 10, 0, 0)
        self.Tetrode_Parameters_Electrode_Spacing_frame = QFrame(self.Tetrode_Parameters_Electrode_Position_frame)
        self.Tetrode_Parameters_Electrode_Spacing_frame.setObjectName(u"Tetrode_Parameters_Electrode_Spacing_frame")
        self.Tetrode_Parameters_Electrode_Spacing_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Electrode_Spacing_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_16 = QHBoxLayout(self.Tetrode_Parameters_Electrode_Spacing_frame)
        self.horizontalLayout_16.setSpacing(0)
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.horizontalLayout_16.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_Electrode_Spacing_label = QLabel(self.Tetrode_Parameters_Electrode_Spacing_frame)
        self.Tetrode_Parameters_Electrode_Spacing_label.setObjectName(u"Tetrode_Parameters_Electrode_Spacing_label")

        self.horizontalLayout_16.addWidget(self.Tetrode_Parameters_Electrode_Spacing_label)

        self.Tetrode_Parameters_Electrode_Spacing_doubleSpinBox = QDoubleSpinBox(self.Tetrode_Parameters_Electrode_Spacing_frame)
        self.Tetrode_Parameters_Electrode_Spacing_doubleSpinBox.setObjectName(u"Tetrode_Parameters_Electrode_Spacing_doubleSpinBox")
        self.Tetrode_Parameters_Electrode_Spacing_doubleSpinBox.setDecimals(1)
        self.Tetrode_Parameters_Electrode_Spacing_doubleSpinBox.setMinimum(1.000000000000000)
        self.Tetrode_Parameters_Electrode_Spacing_doubleSpinBox.setMaximum(50.000000000000000)
        self.Tetrode_Parameters_Electrode_Spacing_doubleSpinBox.setValue(25.000000000000000)

        self.horizontalLayout_16.addWidget(self.Tetrode_Parameters_Electrode_Spacing_doubleSpinBox)


        self.horizontalLayout_7.addWidget(self.Tetrode_Parameters_Electrode_Spacing_frame, 0, Qt.AlignLeft)

        self.Tetrode_Parameters_View_SnaToGrid_frame = QFrame(self.Tetrode_Parameters_Electrode_Position_frame)
        self.Tetrode_Parameters_View_SnaToGrid_frame.setObjectName(u"Tetrode_Parameters_View_SnaToGrid_frame")
        self.Tetrode_Parameters_View_SnaToGrid_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_View_SnaToGrid_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_17 = QHBoxLayout(self.Tetrode_Parameters_View_SnaToGrid_frame)
        self.horizontalLayout_17.setSpacing(0)
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.horizontalLayout_17.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_View_SnaToGrid_pushButton = QPushButton(self.Tetrode_Parameters_View_SnaToGrid_frame)
        self.Tetrode_Parameters_View_SnaToGrid_pushButton.setObjectName(u"Tetrode_Parameters_View_SnaToGrid_pushButton")
        self.Tetrode_Parameters_View_SnaToGrid_pushButton.setCheckable(False)

        self.horizontalLayout_17.addWidget(self.Tetrode_Parameters_View_SnaToGrid_pushButton)


        self.horizontalLayout_7.addWidget(self.Tetrode_Parameters_View_SnaToGrid_frame)


        self.verticalLayout_13.addWidget(self.Tetrode_Parameters_Electrode_Position_frame)

        self.Tetrode_Parameters_Electrode_Rot_frame = QFrame(self.Tetrode_Parameters_Electrode_groupBox)
        self.Tetrode_Parameters_Electrode_Rot_frame.setObjectName(u"Tetrode_Parameters_Electrode_Rot_frame")
        self.Tetrode_Parameters_Electrode_Rot_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Electrode_Rot_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_15 = QVBoxLayout(self.Tetrode_Parameters_Electrode_Rot_frame)
        self.verticalLayout_15.setSpacing(5)
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.verticalLayout_15.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_Electrode_Rot_label = QLabel(self.Tetrode_Parameters_Electrode_Rot_frame)
        self.Tetrode_Parameters_Electrode_Rot_label.setObjectName(u"Tetrode_Parameters_Electrode_Rot_label")

        self.verticalLayout_15.addWidget(self.Tetrode_Parameters_Electrode_Rot_label)

        self.Tetrode_Parameters_Electrode_RotCoordinate_frame = QFrame(self.Tetrode_Parameters_Electrode_Rot_frame)
        self.Tetrode_Parameters_Electrode_RotCoordinate_frame.setObjectName(u"Tetrode_Parameters_Electrode_RotCoordinate_frame")
        self.Tetrode_Parameters_Electrode_RotCoordinate_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Electrode_RotCoordinate_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_6 = QHBoxLayout(self.Tetrode_Parameters_Electrode_RotCoordinate_frame)
        self.horizontalLayout_6.setSpacing(5)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_Electrode_Rotx_label = QLabel(self.Tetrode_Parameters_Electrode_RotCoordinate_frame)
        self.Tetrode_Parameters_Electrode_Rotx_label.setObjectName(u"Tetrode_Parameters_Electrode_Rotx_label")

        self.horizontalLayout_6.addWidget(self.Tetrode_Parameters_Electrode_Rotx_label, 0, Qt.AlignHCenter)

        self.Tetrode_Parameters_Electrode_Rotx_spinBox = QSpinBox(self.Tetrode_Parameters_Electrode_RotCoordinate_frame)
        self.Tetrode_Parameters_Electrode_Rotx_spinBox.setObjectName(u"Tetrode_Parameters_Electrode_Rotx_spinBox")
        self.Tetrode_Parameters_Electrode_Rotx_spinBox.setMinimum(-90)
        self.Tetrode_Parameters_Electrode_Rotx_spinBox.setMaximum(90)

        self.horizontalLayout_6.addWidget(self.Tetrode_Parameters_Electrode_Rotx_spinBox)

        self.Tetrode_Parameters_Electrode_Roty_label = QLabel(self.Tetrode_Parameters_Electrode_RotCoordinate_frame)
        self.Tetrode_Parameters_Electrode_Roty_label.setObjectName(u"Tetrode_Parameters_Electrode_Roty_label")

        self.horizontalLayout_6.addWidget(self.Tetrode_Parameters_Electrode_Roty_label, 0, Qt.AlignHCenter)

        self.Tetrode_Parameters_Electrode_Roty_spinBox = QSpinBox(self.Tetrode_Parameters_Electrode_RotCoordinate_frame)
        self.Tetrode_Parameters_Electrode_Roty_spinBox.setObjectName(u"Tetrode_Parameters_Electrode_Roty_spinBox")
        self.Tetrode_Parameters_Electrode_Roty_spinBox.setMinimum(-90)
        self.Tetrode_Parameters_Electrode_Roty_spinBox.setMaximum(90)

        self.horizontalLayout_6.addWidget(self.Tetrode_Parameters_Electrode_Roty_spinBox)

        self.Tetrode_Parameters_Electrode_Rotz_label = QLabel(self.Tetrode_Parameters_Electrode_RotCoordinate_frame)
        self.Tetrode_Parameters_Electrode_Rotz_label.setObjectName(u"Tetrode_Parameters_Electrode_Rotz_label")

        self.horizontalLayout_6.addWidget(self.Tetrode_Parameters_Electrode_Rotz_label, 0, Qt.AlignHCenter)

        self.Tetrode_Parameters_Electrode_Rotz_spinBox = QSpinBox(self.Tetrode_Parameters_Electrode_RotCoordinate_frame)
        self.Tetrode_Parameters_Electrode_Rotz_spinBox.setObjectName(u"Tetrode_Parameters_Electrode_Rotz_spinBox")
        self.Tetrode_Parameters_Electrode_Rotz_spinBox.setMinimum(-90)
        self.Tetrode_Parameters_Electrode_Rotz_spinBox.setMaximum(90)
        self.Tetrode_Parameters_Electrode_Rotz_spinBox.setStepType(QAbstractSpinBox.DefaultStepType)

        self.horizontalLayout_6.addWidget(self.Tetrode_Parameters_Electrode_Rotz_spinBox)


        self.verticalLayout_15.addWidget(self.Tetrode_Parameters_Electrode_RotCoordinate_frame)


        self.verticalLayout_13.addWidget(self.Tetrode_Parameters_Electrode_Rot_frame)


        self.verticalLayout_5.addWidget(self.Tetrode_Parameters_Electrode_groupBox)

        self.line_2 = QFrame(self.Tetrode_Parameters_frame)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setStyleSheet(u"background-color: rgb(0, 43, 54);")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_5.addWidget(self.line_2)

        self.Tetrode_Parameters_View_groupBox = QGroupBox(self.Tetrode_Parameters_frame)
        self.Tetrode_Parameters_View_groupBox.setObjectName(u"Tetrode_Parameters_View_groupBox")
        self.verticalLayout_16 = QVBoxLayout(self.Tetrode_Parameters_View_groupBox)
        self.verticalLayout_16.setSpacing(20)
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.verticalLayout_16.setContentsMargins(10, 0, 10, 10)
        self.Tetrode_Parameters_View_label_frame = QFrame(self.Tetrode_Parameters_View_groupBox)
        self.Tetrode_Parameters_View_label_frame.setObjectName(u"Tetrode_Parameters_View_label_frame")
        self.Tetrode_Parameters_View_label_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_View_label_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_17 = QVBoxLayout(self.Tetrode_Parameters_View_label_frame)
        self.verticalLayout_17.setSpacing(0)
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.verticalLayout_17.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_View_label = QLabel(self.Tetrode_Parameters_View_label_frame)
        self.Tetrode_Parameters_View_label.setObjectName(u"Tetrode_Parameters_View_label")
        self.Tetrode_Parameters_View_label.setFont(font1)

        self.verticalLayout_17.addWidget(self.Tetrode_Parameters_View_label)


        self.verticalLayout_16.addWidget(self.Tetrode_Parameters_View_label_frame)

        self.Tetrode_Parameters_View_GridSize_frame = QFrame(self.Tetrode_Parameters_View_groupBox)
        self.Tetrode_Parameters_View_GridSize_frame.setObjectName(u"Tetrode_Parameters_View_GridSize_frame")
        self.Tetrode_Parameters_View_GridSize_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_View_GridSize_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_8 = QHBoxLayout(self.Tetrode_Parameters_View_GridSize_frame)
        self.horizontalLayout_8.setSpacing(10)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(10, 0, 0, 0)
        self.Tetrode_Parameters_View_GridSize_label = QLabel(self.Tetrode_Parameters_View_GridSize_frame)
        self.Tetrode_Parameters_View_GridSize_label.setObjectName(u"Tetrode_Parameters_View_GridSize_label")

        self.horizontalLayout_8.addWidget(self.Tetrode_Parameters_View_GridSize_label)

        self.Tetrode_Parameters_View_GridSize_doubleSpinBox = QDoubleSpinBox(self.Tetrode_Parameters_View_GridSize_frame)
        self.Tetrode_Parameters_View_GridSize_doubleSpinBox.setObjectName(u"Tetrode_Parameters_View_GridSize_doubleSpinBox")
        self.Tetrode_Parameters_View_GridSize_doubleSpinBox.setDecimals(1)
        self.Tetrode_Parameters_View_GridSize_doubleSpinBox.setSingleStep(0.500000000000000)
        self.Tetrode_Parameters_View_GridSize_doubleSpinBox.setValue(1.000000000000000)

        self.horizontalLayout_8.addWidget(self.Tetrode_Parameters_View_GridSize_doubleSpinBox)


        self.verticalLayout_16.addWidget(self.Tetrode_Parameters_View_GridSize_frame, 0, Qt.AlignLeft)

        self.Tetrode_Parameters_View_Options_frame = QFrame(self.Tetrode_Parameters_View_groupBox)
        self.Tetrode_Parameters_View_Options_frame.setObjectName(u"Tetrode_Parameters_View_Options_frame")
        self.Tetrode_Parameters_View_Options_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_View_Options_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.Tetrode_Parameters_View_Options_frame)
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_View_ShowLabels_checkBox = QCheckBox(self.Tetrode_Parameters_View_Options_frame)
        self.Tetrode_Parameters_View_ShowLabels_checkBox.setObjectName(u"Tetrode_Parameters_View_ShowLabels_checkBox")
        self.Tetrode_Parameters_View_ShowLabels_checkBox.setChecked(True)

        self.verticalLayout.addWidget(self.Tetrode_Parameters_View_ShowLabels_checkBox)

        self.Tetrode_Parameters_View_ShowDistance_checkBox = QCheckBox(self.Tetrode_Parameters_View_Options_frame)
        self.Tetrode_Parameters_View_ShowDistance_checkBox.setObjectName(u"Tetrode_Parameters_View_ShowDistance_checkBox")

        self.verticalLayout.addWidget(self.Tetrode_Parameters_View_ShowDistance_checkBox)


        self.verticalLayout_16.addWidget(self.Tetrode_Parameters_View_Options_frame)

        self.Tetrode_Parameters_View_pushButton_frame = QFrame(self.Tetrode_Parameters_View_groupBox)
        self.Tetrode_Parameters_View_pushButton_frame.setObjectName(u"Tetrode_Parameters_View_pushButton_frame")
        self.Tetrode_Parameters_View_pushButton_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_View_pushButton_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_11 = QHBoxLayout(self.Tetrode_Parameters_View_pushButton_frame)
        self.horizontalLayout_11.setSpacing(10)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_Parameters_View_Center_pushButton = QPushButton(self.Tetrode_Parameters_View_pushButton_frame)
        self.Tetrode_Parameters_View_Center_pushButton.setObjectName(u"Tetrode_Parameters_View_Center_pushButton")
        self.Tetrode_Parameters_View_Center_pushButton.setMinimumSize(QSize(125, 0))
        font2 = QFont()
        font2.setPointSize(10)
        font2.setBold(True)
        self.Tetrode_Parameters_View_Center_pushButton.setFont(font2)

        self.horizontalLayout_11.addWidget(self.Tetrode_Parameters_View_Center_pushButton)

        self.Tetrode_Parameters_View_RFeset_pushButton = QPushButton(self.Tetrode_Parameters_View_pushButton_frame)
        self.Tetrode_Parameters_View_RFeset_pushButton.setObjectName(u"Tetrode_Parameters_View_RFeset_pushButton")
        self.Tetrode_Parameters_View_RFeset_pushButton.setMinimumSize(QSize(125, 0))
        self.Tetrode_Parameters_View_RFeset_pushButton.setFont(font2)

        self.horizontalLayout_11.addWidget(self.Tetrode_Parameters_View_RFeset_pushButton)


        self.verticalLayout_16.addWidget(self.Tetrode_Parameters_View_pushButton_frame)


        self.verticalLayout_5.addWidget(self.Tetrode_Parameters_View_groupBox)


        self.horizontalLayout.addWidget(self.Tetrode_Parameters_frame)

        self.Tetrode_Graphic_frame = QFrame(self.Tetrode_Center_frame)
        self.Tetrode_Graphic_frame.setObjectName(u"Tetrode_Graphic_frame")
        self.Tetrode_Graphic_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Graphic_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.Tetrode_Graphic_frame)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.Tetrode_graphicsView = GeometryView(self.Tetrode_Graphic_frame)
        self.Tetrode_graphicsView.setObjectName(u"Tetrode_graphicsView")
        self.Tetrode_graphicsView.setMinimumSize(QSize(800, 450))

        self.verticalLayout_4.addWidget(self.Tetrode_graphicsView)

        self.Tetrode_Bottom_frame = QFrame(self.Tetrode_Graphic_frame)
        self.Tetrode_Bottom_frame.setObjectName(u"Tetrode_Bottom_frame")
        self.Tetrode_Bottom_frame.setMinimumSize(QSize(0, 100))
        self.Tetrode_Bottom_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Bottom_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_18 = QHBoxLayout(self.Tetrode_Bottom_frame)
        self.horizontalLayout_18.setSpacing(0)
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.horizontalLayout_18.setContentsMargins(0, 0, 0, 0)
        self.line_3 = QFrame(self.Tetrode_Bottom_frame)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setStyleSheet(u"background-color: rgb(0, 43, 54);")
        self.line_3.setFrameShape(QFrame.Shape.VLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout_18.addWidget(self.line_3)

        self.Tetrode_Parameters_Readout_frame = QFrame(self.Tetrode_Bottom_frame)
        self.Tetrode_Parameters_Readout_frame.setObjectName(u"Tetrode_Parameters_Readout_frame")
        self.Tetrode_Parameters_Readout_frame.setMinimumSize(QSize(0, 0))
        self.Tetrode_Parameters_Readout_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Readout_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_19 = QVBoxLayout(self.Tetrode_Parameters_Readout_frame)
        self.verticalLayout_19.setSpacing(5)
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.verticalLayout_19.setContentsMargins(20, 10, 0, 10)
        self.Tetrode_Parameters_Readout_Cursor_frame = QFrame(self.Tetrode_Parameters_Readout_frame)
        self.Tetrode_Parameters_Readout_Cursor_frame.setObjectName(u"Tetrode_Parameters_Readout_Cursor_frame")
        self.Tetrode_Parameters_Readout_Cursor_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Readout_Cursor_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_12 = QHBoxLayout(self.Tetrode_Parameters_Readout_Cursor_frame)
        self.horizontalLayout_12.setSpacing(10)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalLayout_12.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_19.addWidget(self.Tetrode_Parameters_Readout_Cursor_frame, 0, Qt.AlignLeft)

        self.Tetrode_Parameters_Readout_Selected_frame = QFrame(self.Tetrode_Parameters_Readout_frame)
        self.Tetrode_Parameters_Readout_Selected_frame.setObjectName(u"Tetrode_Parameters_Readout_Selected_frame")
        self.Tetrode_Parameters_Readout_Selected_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Readout_Selected_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_13 = QHBoxLayout(self.Tetrode_Parameters_Readout_Selected_frame)
        self.horizontalLayout_13.setSpacing(10)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalLayout_13.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_19.addWidget(self.Tetrode_Parameters_Readout_Selected_frame, 0, Qt.AlignLeft)

        self.Tetrode_Parameters_Readout_Zoom_frame = QFrame(self.Tetrode_Parameters_Readout_frame)
        self.Tetrode_Parameters_Readout_Zoom_frame.setObjectName(u"Tetrode_Parameters_Readout_Zoom_frame")
        self.Tetrode_Parameters_Readout_Zoom_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Parameters_Readout_Zoom_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_14 = QHBoxLayout(self.Tetrode_Parameters_Readout_Zoom_frame)
        self.horizontalLayout_14.setSpacing(10)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.horizontalLayout_14.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_19.addWidget(self.Tetrode_Parameters_Readout_Zoom_frame, 0, Qt.AlignLeft)


        self.horizontalLayout_18.addWidget(self.Tetrode_Parameters_Readout_frame)

        self.Tetrode_Distance_Readout_Neuron1_frame = QFrame(self.Tetrode_Bottom_frame)
        self.Tetrode_Distance_Readout_Neuron1_frame.setObjectName(u"Tetrode_Distance_Readout_Neuron1_frame")
        self.Tetrode_Distance_Readout_Neuron1_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Distance_Readout_Neuron1_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_22 = QVBoxLayout(self.Tetrode_Distance_Readout_Neuron1_frame)
        self.verticalLayout_22.setSpacing(0)
        self.verticalLayout_22.setObjectName(u"verticalLayout_22")
        self.verticalLayout_22.setContentsMargins(0, 0, 0, 0)

        self.horizontalLayout_18.addWidget(self.Tetrode_Distance_Readout_Neuron1_frame)

        self.Tetrode_Distance_Readout_Neuron2_frame = QFrame(self.Tetrode_Bottom_frame)
        self.Tetrode_Distance_Readout_Neuron2_frame.setObjectName(u"Tetrode_Distance_Readout_Neuron2_frame")
        self.Tetrode_Distance_Readout_Neuron2_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Distance_Readout_Neuron2_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_21 = QVBoxLayout(self.Tetrode_Distance_Readout_Neuron2_frame)
        self.verticalLayout_21.setSpacing(0)
        self.verticalLayout_21.setObjectName(u"verticalLayout_21")
        self.verticalLayout_21.setContentsMargins(0, 0, 0, 0)

        self.horizontalLayout_18.addWidget(self.Tetrode_Distance_Readout_Neuron2_frame)

        self.Tetrode_Distance_Readout_Neuron3_frame = QFrame(self.Tetrode_Bottom_frame)
        self.Tetrode_Distance_Readout_Neuron3_frame.setObjectName(u"Tetrode_Distance_Readout_Neuron3_frame")
        self.Tetrode_Distance_Readout_Neuron3_frame.setFrameShape(QFrame.StyledPanel)
        self.Tetrode_Distance_Readout_Neuron3_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_20 = QVBoxLayout(self.Tetrode_Distance_Readout_Neuron3_frame)
        self.verticalLayout_20.setSpacing(0)
        self.verticalLayout_20.setObjectName(u"verticalLayout_20")
        self.verticalLayout_20.setContentsMargins(0, 0, 0, 0)

        self.horizontalLayout_18.addWidget(self.Tetrode_Distance_Readout_Neuron3_frame)


        self.verticalLayout_4.addWidget(self.Tetrode_Bottom_frame)


        self.horizontalLayout.addWidget(self.Tetrode_Graphic_frame)


        self.verticalLayout_3.addWidget(self.Tetrode_Center_frame)


        self.horizontalLayout_9.addWidget(self.Tetrode_Main_frame)

        Tetrode.setCentralWidget(self.centralwidget)

        self.retranslateUi(Tetrode)

        QMetaObject.connectSlotsByName(Tetrode)
    # setupUi

    def retranslateUi(self, Tetrode):
        Tetrode.setWindowTitle(QCoreApplication.translate("Tetrode", u"MainWindow", None))
        self.Tetrode_Header_label.setText(QCoreApplication.translate("Tetrode", u"Extracellular Geometry view", None))
        self.Tetrode_Close_pushButton.setText("")
        self.Tetrode_Parameters_Spikeling1_label.setText(QCoreApplication.translate("Tetrode", u"Main Neuron", None))
        self.Tetrode_Parameters_Spikeling1_x_label.setText(QCoreApplication.translate("Tetrode", u"X", None))
        self.Tetrode_Parameters_Spikeling1_x_doubleSpinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b5m", None))
        self.Tetrode_Parameters_Spikeling1_y_label.setText(QCoreApplication.translate("Tetrode", u"Y", None))
        self.Tetrode_Parameters_Spikeling1_y_doubleSpinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b5m", None))
        self.Tetrode_Parameters_Spikeling1_z_label.setText(QCoreApplication.translate("Tetrode", u"Z", None))
        self.Tetrode_Parameters_Spikeling1_z_doubleSpinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b5m", None))
        self.Tetrode_Parameters_Spikeling2_label.setText(QCoreApplication.translate("Tetrode", u"Auxiliary Neuron 1", None))
        self.Tetrode_Parameters_Spikeling2_x_label.setText(QCoreApplication.translate("Tetrode", u"X", None))
        self.Tetrode_Parameters_Spikeling2_x_doubleSpinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b5m", None))
        self.Tetrode_Parameters_Spikeling2_y_label.setText(QCoreApplication.translate("Tetrode", u"Y", None))
        self.Tetrode_Parameters_Spikeling2_y_doubleSpinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b5m", None))
        self.Tetrode_Parameters_Spikeling2_z_label.setText(QCoreApplication.translate("Tetrode", u"Z", None))
        self.Tetrode_Parameters_Spikeling2_z_doubleSpinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b5m", None))
        self.Tetrode_Parameters_Spikeling3_label.setText(QCoreApplication.translate("Tetrode", u"Auxiliary Neuron 2", None))
        self.Tetrode_Parameters_Spikeling3_x_label.setText(QCoreApplication.translate("Tetrode", u"X", None))
        self.Tetrode_Parameters_Spikeling3_x_doubleSpinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b5m", None))
        self.Tetrode_Parameters_Spikeling3_y_label.setText(QCoreApplication.translate("Tetrode", u"Y", None))
        self.Tetrode_Parameters_Spikeling3_y_doubleSpinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b5m", None))
        self.Tetrode_Parameters_Spikeling3_z_label.setText(QCoreApplication.translate("Tetrode", u"Z", None))
        self.Tetrode_Parameters_Spikeling3_z_doubleSpinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b5m", None))
        self.Tetrode_Parameters_Electrode_label.setText(QCoreApplication.translate("Tetrode", u"Electrode", None))
        self.Tetrode_Parameters_Electrode_x_label.setText(QCoreApplication.translate("Tetrode", u"X", None))
        self.Tetrode_Parameters_Electrode_x_doubleSpinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b5m", None))
        self.Tetrode_Parameters_Electrode_y_label.setText(QCoreApplication.translate("Tetrode", u"Y", None))
        self.Tetrode_Parameters_Electrode_y_doubleSpinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b5m", None))
        self.Tetrode_Parameters_Electrode_z_label.setText(QCoreApplication.translate("Tetrode", u"Z", None))
        self.Tetrode_Parameters_Electrode_z_doubleSpinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b5m ", None))
        self.Tetrode_Parameters_Electrode_Spacing_label.setText(QCoreApplication.translate("Tetrode", u"Contact spacing", None))
        self.Tetrode_Parameters_Electrode_Spacing_doubleSpinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b5m", None))
        self.Tetrode_Parameters_View_SnaToGrid_pushButton.setText(QCoreApplication.translate("Tetrode", u"Snap to Grid", None))
        self.Tetrode_Parameters_Electrode_Rot_label.setText(QCoreApplication.translate("Tetrode", u"Rotation", None))
        self.Tetrode_Parameters_Electrode_Rotx_label.setText(QCoreApplication.translate("Tetrode", u"X", None))
        self.Tetrode_Parameters_Electrode_Rotx_spinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b0", None))
        self.Tetrode_Parameters_Electrode_Roty_label.setText(QCoreApplication.translate("Tetrode", u"Y", None))
        self.Tetrode_Parameters_Electrode_Roty_spinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b0", None))
        self.Tetrode_Parameters_Electrode_Rotz_label.setText(QCoreApplication.translate("Tetrode", u"Z", None))
        self.Tetrode_Parameters_Electrode_Rotz_spinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b0", None))
        self.Tetrode_Parameters_View_label.setText(QCoreApplication.translate("Tetrode", u"View Options", None))
        self.Tetrode_Parameters_View_GridSize_label.setText(QCoreApplication.translate("Tetrode", u"Grid Size", None))
        self.Tetrode_Parameters_View_GridSize_doubleSpinBox.setSuffix(QCoreApplication.translate("Tetrode", u" \u00b5m", None))
        self.Tetrode_Parameters_View_ShowLabels_checkBox.setText(QCoreApplication.translate("Tetrode", u"Show Labels", None))
        self.Tetrode_Parameters_View_ShowDistance_checkBox.setText(QCoreApplication.translate("Tetrode", u"Show Distance Lines", None))
        self.Tetrode_Parameters_View_Center_pushButton.setText(QCoreApplication.translate("Tetrode", u"Center on Electrode", None))
        self.Tetrode_Parameters_View_RFeset_pushButton.setText(QCoreApplication.translate("Tetrode", u"Reset", None))
    # retranslateUi

