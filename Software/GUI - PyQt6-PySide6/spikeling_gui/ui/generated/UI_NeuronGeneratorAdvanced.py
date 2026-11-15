# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'UI_NeuronGeneratorAdvanced.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QFormLayout, QGroupBox, QLabel, QLineEdit,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_NeuronGeneratorAdvanced(object):
    def setupUi(self, NeuronGeneratorAdvanced):
        if not NeuronGeneratorAdvanced.objectName():
            NeuronGeneratorAdvanced.setObjectName(u"NeuronGeneratorAdvanced")
        self.dialogLayout = QVBoxLayout(NeuronGeneratorAdvanced)
        self.dialogLayout.setObjectName(u"dialogLayout")
        self.photoGainGroup = QGroupBox(NeuronGeneratorAdvanced)
        self.photoGainGroup.setObjectName(u"photoGainGroup")
        self.photoGainGroup.setProperty(u"themeBox", True)
        self.photoGainLayout = QFormLayout(self.photoGainGroup)
        self.photoGainLayout.setObjectName(u"photoGainLayout")
        self.photoGainLayout.setVerticalSpacing(6)
        self.photoGainLayout.setHorizontalSpacing(12)
        self.photoGainLayout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.photoGainLabel = QLabel(self.photoGainGroup)
        self.photoGainLabel.setObjectName(u"photoGainLabel")
        self.photoGainLabel.setWordWrap(True)
        self.photoGainLabel.setMinimumSize(QSize(176, 0))

        self.photoGainLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.photoGainLabel)

        self.photoGain = QLineEdit(self.photoGainGroup)
        self.photoGain.setObjectName(u"photoGain")
        self.photoGain.setMinimumSize(QSize(116, 0))

        self.photoGainLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.photoGain)

        self.photoDecayLabel = QLabel(self.photoGainGroup)
        self.photoDecayLabel.setObjectName(u"photoDecayLabel")
        self.photoDecayLabel.setWordWrap(True)
        self.photoDecayLabel.setMinimumSize(QSize(176, 0))

        self.photoGainLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.photoDecayLabel)

        self.photoDecay = QLineEdit(self.photoGainGroup)
        self.photoDecay.setObjectName(u"photoDecay")
        self.photoDecay.setMinimumSize(QSize(116, 0))

        self.photoGainLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.photoDecay)

        self.photoRecoveryLabel = QLabel(self.photoGainGroup)
        self.photoRecoveryLabel.setObjectName(u"photoRecoveryLabel")
        self.photoRecoveryLabel.setWordWrap(True)
        self.photoRecoveryLabel.setMinimumSize(QSize(176, 0))

        self.photoGainLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.photoRecoveryLabel)

        self.photoRecovery = QLineEdit(self.photoGainGroup)
        self.photoRecovery.setObjectName(u"photoRecovery")
        self.photoRecovery.setMinimumSize(QSize(116, 0))

        self.photoGainLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.photoRecovery)


        self.dialogLayout.addWidget(self.photoGainGroup)

        self.syn1GainGroup = QGroupBox(NeuronGeneratorAdvanced)
        self.syn1GainGroup.setObjectName(u"syn1GainGroup")
        self.syn1GainGroup.setProperty(u"themeBox", True)
        self.syn1GainLayout = QFormLayout(self.syn1GainGroup)
        self.syn1GainLayout.setObjectName(u"syn1GainLayout")
        self.syn1GainLayout.setVerticalSpacing(6)
        self.syn1GainLayout.setHorizontalSpacing(12)
        self.syn1GainLayout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.syn1GainLabel = QLabel(self.syn1GainGroup)
        self.syn1GainLabel.setObjectName(u"syn1GainLabel")
        self.syn1GainLabel.setWordWrap(True)
        self.syn1GainLabel.setMinimumSize(QSize(176, 0))

        self.syn1GainLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.syn1GainLabel)

        self.syn1Gain = QLineEdit(self.syn1GainGroup)
        self.syn1Gain.setObjectName(u"syn1Gain")
        self.syn1Gain.setMinimumSize(QSize(116, 0))

        self.syn1GainLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.syn1Gain)

        self.syn1DecayLabel = QLabel(self.syn1GainGroup)
        self.syn1DecayLabel.setObjectName(u"syn1DecayLabel")
        self.syn1DecayLabel.setWordWrap(True)
        self.syn1DecayLabel.setMinimumSize(QSize(176, 0))

        self.syn1GainLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.syn1DecayLabel)

        self.syn1Decay = QLineEdit(self.syn1GainGroup)
        self.syn1Decay.setObjectName(u"syn1Decay")
        self.syn1Decay.setMinimumSize(QSize(116, 0))

        self.syn1GainLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.syn1Decay)


        self.dialogLayout.addWidget(self.syn1GainGroup)

        self.syn2GainGroup = QGroupBox(NeuronGeneratorAdvanced)
        self.syn2GainGroup.setObjectName(u"syn2GainGroup")
        self.syn2GainGroup.setProperty(u"themeBox", True)
        self.syn2GainLayout = QFormLayout(self.syn2GainGroup)
        self.syn2GainLayout.setObjectName(u"syn2GainLayout")
        self.syn2GainLayout.setVerticalSpacing(6)
        self.syn2GainLayout.setHorizontalSpacing(12)
        self.syn2GainLayout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.syn2GainLabel = QLabel(self.syn2GainGroup)
        self.syn2GainLabel.setObjectName(u"syn2GainLabel")
        self.syn2GainLabel.setWordWrap(True)
        self.syn2GainLabel.setMinimumSize(QSize(176, 0))

        self.syn2GainLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.syn2GainLabel)

        self.syn2Gain = QLineEdit(self.syn2GainGroup)
        self.syn2Gain.setObjectName(u"syn2Gain")
        self.syn2Gain.setMinimumSize(QSize(116, 0))

        self.syn2GainLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.syn2Gain)

        self.syn2DecayLabel = QLabel(self.syn2GainGroup)
        self.syn2DecayLabel.setObjectName(u"syn2DecayLabel")
        self.syn2DecayLabel.setWordWrap(True)
        self.syn2DecayLabel.setMinimumSize(QSize(176, 0))

        self.syn2GainLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.syn2DecayLabel)

        self.syn2Decay = QLineEdit(self.syn2GainGroup)
        self.syn2Decay.setObjectName(u"syn2Decay")
        self.syn2Decay.setMinimumSize(QSize(116, 0))

        self.syn2GainLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.syn2Decay)


        self.dialogLayout.addWidget(self.syn2GainGroup)

        self.validationMessage = QLabel(NeuronGeneratorAdvanced)
        self.validationMessage.setObjectName(u"validationMessage")
        self.validationMessage.setWordWrap(True)

        self.dialogLayout.addWidget(self.validationMessage)

        self.buttonBox = QDialogButtonBox(NeuronGeneratorAdvanced)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.RestoreDefaults)

        self.dialogLayout.addWidget(self.buttonBox)

#if QT_CONFIG(shortcut)
        self.photoGainLabel.setBuddy(self.photoGain)
        self.photoDecayLabel.setBuddy(self.photoDecay)
        self.photoRecoveryLabel.setBuddy(self.photoRecovery)
        self.syn1GainLabel.setBuddy(self.syn1Gain)
        self.syn1DecayLabel.setBuddy(self.syn1Decay)
        self.syn2GainLabel.setBuddy(self.syn2Gain)
        self.syn2DecayLabel.setBuddy(self.syn2Decay)
#endif // QT_CONFIG(shortcut)

        self.retranslateUi(NeuronGeneratorAdvanced)

        QMetaObject.connectSlotsByName(NeuronGeneratorAdvanced)
    # setupUi

    def retranslateUi(self, NeuronGeneratorAdvanced):
        NeuronGeneratorAdvanced.setWindowTitle(QCoreApplication.translate("NeuronGeneratorAdvanced", u"Advanced neuron parameters", None))
        self.photoGainGroup.setTitle(QCoreApplication.translate("NeuronGeneratorAdvanced", u"Photoreceptor", None))
        self.photoGainLabel.setText(QCoreApplication.translate("NeuronGeneratorAdvanced", u"Gain (%)", None))
        self.photoDecayLabel.setText(QCoreApplication.translate("NeuronGeneratorAdvanced", u"Decay (ms\u207b\u00b9)", None))
        self.photoRecoveryLabel.setText(QCoreApplication.translate("NeuronGeneratorAdvanced", u"Recovery (ms\u207b\u00b9)", None))
        self.syn1GainGroup.setTitle(QCoreApplication.translate("NeuronGeneratorAdvanced", u"Synapse 1", None))
        self.syn1GainLabel.setText(QCoreApplication.translate("NeuronGeneratorAdvanced", u"Gain (%)", None))
#if QT_CONFIG(tooltip)
        self.syn1DecayLabel.setToolTip(QCoreApplication.translate("NeuronGeneratorAdvanced", u"Fraction of synaptic current retained after each update.", None))
#endif // QT_CONFIG(tooltip)
        self.syn1DecayLabel.setText(QCoreApplication.translate("NeuronGeneratorAdvanced", u"Current retention (0 to 1)", None))
        self.syn2GainGroup.setTitle(QCoreApplication.translate("NeuronGeneratorAdvanced", u"Synapse 2", None))
        self.syn2GainLabel.setText(QCoreApplication.translate("NeuronGeneratorAdvanced", u"Gain (%)", None))
#if QT_CONFIG(tooltip)
        self.syn2DecayLabel.setToolTip(QCoreApplication.translate("NeuronGeneratorAdvanced", u"Fraction of synaptic current retained after each update.", None))
#endif // QT_CONFIG(tooltip)
        self.syn2DecayLabel.setText(QCoreApplication.translate("NeuronGeneratorAdvanced", u"Current retention (0 to 1)", None))
    # retranslateUi
