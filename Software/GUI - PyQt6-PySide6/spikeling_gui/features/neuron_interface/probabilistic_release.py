"""Advanced settings for the firmware's probabilistic release model."""

from PySide6.QtCore import QCoreApplication, QLocale, QRegularExpression
from PySide6.QtGui import QIntValidator, QRegularExpressionValidator
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit

from spikeling_gui.appearance.theme_manager import theme_manager


def edit_release_settings(parent, synapse, sites, seed):
    """Return the validated site count and shared seed, or None on cancel."""
    def tr(text):
        return QCoreApplication.translate("ProbabilisticRelease", text)

    dialog = QDialog(parent)
    dialog.setWindowTitle(tr("Synapse {synapse} · Advanced Release Settings").format(synapse=synapse))
    dialog.setStyleSheet(theme_manager.stylesheet())
    form = QFormLayout(dialog)

    sites_field = QLineEdit(str(sites), dialog)
    sites_validator = QIntValidator(1, 128, sites_field)
    locale = QLocale.c()
    locale.setNumberOptions(QLocale.NumberOption.RejectGroupSeparator)
    sites_validator.setLocale(locale)
    sites_field.setValidator(sites_validator)
    form.addRow(tr("Release sites"), sites_field)

    seed_field = QLineEdit(str(seed), dialog)
    seed_field.setValidator(QRegularExpressionValidator(
        QRegularExpression("[0-9]{1,10}"), seed_field,
    ))
    form.addRow(tr("Random seed"), seed_field)
    hint = QLabel(tr("The seed is shared by both synapses. Changing it restarts both release sequences."), dialog)
    hint.setWordWrap(True)
    form.addRow(hint)

    status = QLabel(dialog)
    status.setWordWrap(True)
    form.addRow(status)

    def accept_settings():
        if not sites_field.hasAcceptableInput():
            status.setText(tr("Enter a release site count from 1 to 128."))
        elif not seed_field.hasAcceptableInput() or int(seed_field.text()) > 4294967295:
            status.setText(tr("Enter a random seed from 0 to 4294967295."))
        else:
            dialog.accept()

    standard = QDialogButtonBox.StandardButton
    buttons = QDialogButtonBox(standard.Ok | standard.Cancel, dialog)
    buttons.accepted.connect(accept_settings)
    buttons.rejected.connect(dialog.reject)
    form.addRow(buttons)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return int(sites_field.text()), int(seed_field.text())
    return None
