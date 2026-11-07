"""Non-experimental preferences and startup translation loading."""
from pathlib import Path
import sys
from PySide6.QtCore import QLibraryInfo, QLocale, QSettings, QStandardPaths, QTranslator
from resource_path import resource_path

LANGUAGE_KEY = "general/language"
RECORDING_DIRECTORY_KEY = "recording/default_directory"
LANGUAGES = (("en", "English"), ("fr", "Français"), ("el", "Ελληνικά"),
             ("it", "Italiano"), ("es", "Español"))


def preference_store():
    """Use the same explicit INI scope as the existing theme manager."""
    return QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope,
                     "Spikeling", "SpikelingGUI")


def translation_path(code):
    return resource_path("translations", f"spikeling_{code}.qm")


def language_available(code):
    """Only offer a language whose application catalogue can actually load."""
    if code == "en":
        return True
    return QTranslator().load(str(translation_path(code)))


def default_recording_directory(settings=None):
    """Resolve the saved default, preserving the previous source-run default."""
    settings = settings if settings is not None else preference_store()
    saved = str(settings.value(RECORDING_DIRECTORY_KEY, "") or "").strip()
    if saved:
        return Path(saved).expanduser()
    if getattr(sys, "frozen", False):
        documents = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        return (Path(documents) if documents else Path.home()) / "Spikeling" / "Recordings"
    return Path(__file__).resolve().parent / "Recordings"


def initialise_language(app, settings=None):
    """Load translations before the splash/main UI; retain their ownership."""
    settings = settings if settings is not None else preference_store()
    code = str(settings.value(LANGUAGE_KEY, "en"))
    translators = []
    effective = "en"
    if code != "en":
        translator = QTranslator(app)
        if translator.load(str(translation_path(code))):
            qt_translator = QTranslator(app)
            qt_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
            if qt_translator.load(QLocale(code), "qtbase", "_", qt_path):
                app.installTranslator(qt_translator)
                translators.append(qt_translator)
            app.installTranslator(translator)
            translators.append(translator)
            effective = code
    app._spikeling_translators = translators
    app._spikeling_language = effective
    return effective
