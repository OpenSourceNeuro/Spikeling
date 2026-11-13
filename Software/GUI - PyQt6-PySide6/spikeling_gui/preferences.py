"""Non-experimental preferences and startup translation loading."""
from PySide6.QtCore import QLibraryInfo, QLocale, QSettings, QTranslator
from spikeling_gui.paths import resource_path

LANGUAGE_KEY = "general/language"
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
