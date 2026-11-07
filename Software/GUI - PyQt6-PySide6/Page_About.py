"""About & Scientific foundations controller.

All layouts live in GUI_UI/UI_About.ui. This module connects navigation, local
search, citations, theme/language updates and read-only version reporting.
ShowPage retains the existing Parameters_NavigationButtons call signature.
"""
from __future__ import annotations

import html
import importlib.metadata
import platform
import sys
from urllib.parse import quote

import PySide6
from PySide6.QtCore import QCoreApplication, QEvent, QObject, Qt, QUrl, QTimer, qVersion
from PySide6.QtGui import QDesktopServices, QPalette, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QButtonGroup, QCommandLinkButton, QListWidgetItem, QPushButton, QWidget, QVBoxLayout

try:
    from GUI_UI.UI_About import Ui_AboutPanel
except ModuleNotFoundError as error:
    if error.name not in ('GUI_UI', 'GUI_UI.UI_About'):
        raise
    from UI_About import Ui_AboutPanel

from about_content import (
    DOCS, REFERENCES, REPOSITORY, REVIEW_COMMIT, SOURCE_ROOT, WEBSITE,
    articles, bibtex, citation, science_text,
)


def app_version():
    try:
        from version import __version__
        return str(__version__)
    except ImportError:
        return QCoreApplication.translate('AboutPage', 'Unavailable')


class AboutPage(QObject):
    """Bind Designer widgets, preserving the selected topic across repeat visits."""

    SECTION_KEYS = ('Project', 'Models', 'References', 'Science', 'Software')
    READING_KEYS = ('overview', 'equations', 'implementation', 'limitations', 'references')

    def __init__(self, parent, manager=None):
        page = getattr(parent.ui, 'page_About', None)
        if page is None:
            page = getattr(parent.ui, 'page_701', None)
        if page is None:
            raise RuntimeError('About host page was not found in UI_Spikeling.')
        super().__init__(page)
        self.host = parent
        self.page = page
        self.ui = Ui_AboutPanel()
        # Installer inserts the layout into UI_Spikeling.ui. The fallback also
        # supports an unmodified main form, using the same generated UI class.
        self._integrated = page.findChild(QWidget, 'About_stack') is not None
        if self._integrated:
            for child in page.findChildren(QObject):
                name = child.objectName()
                if name:
                    setattr(self.ui, name, child)
        else:
            old_layout = page.layout()
            if old_layout is not None:
                while old_layout.count():
                    item = old_layout.takeAt(0)
                    if item.widget() is not None:
                        item.widget().deleteLater()
            else:
                old_layout = QVBoxLayout(page)
            old_layout.setContentsMargins(0, 0, 0, 0)
            panel = QWidget(page)
            self.ui.setupUi(panel)
            old_layout.addWidget(panel)
        self.page.setProperty('aboutPanel', True)
        self._section = 0
        self._topic = 'izhikevich'
        self._reference = 'spikeling'
        self._language_refresh_pending = False
        self._manager = manager
        if manager is None:
            try:
                from theme_manager import theme_manager
                self._manager = theme_manager
            except ImportError:
                # Standalone preview needs only PySide6.
                pass
        self._buttons = QButtonGroup(self)
        self._buttons.setExclusive(True)
        for index, key in enumerate(self.SECTION_KEYS):
            button = getattr(self.ui, 'About_nav' + key)
            self._buttons.addButton(button, index)
        self._buttons.idClicked.connect(self.select_section)
        for index, key in enumerate(self.SECTION_KEYS[1:], 1):
            getattr(self.ui, 'About_card' + key).clicked.connect(
                lambda checked=False, destination=index: self.select_section(destination))
        self.ui.About_izhShortcut.clicked.connect(lambda: self.show_topic('izhikevich'))
        self.ui.About_imagingShortcut.clicked.connect(lambda: self.show_topic('imaging'))
        self.ui.About_citeProject.clicked.connect(lambda: self.show_reference('spikeling'))
        self.ui.About_modelSearch.textChanged.connect(self._populate_models)
        self.ui.About_modelList.currentItemChanged.connect(self._topic_changed)
        self.ui.About_referenceSearch.textChanged.connect(self._populate_references)
        self.ui.About_referenceList.currentItemChanged.connect(self._reference_changed)
        self.ui.About_viewSource.clicked.connect(self.view_source)
        self.ui.About_OpenPaper.clicked.connect(self.open_paper)
        self.ui.About_CopyCitation.clicked.connect(self.copy_citation)
        self.ui.About_CopyBibtex.clicked.connect(self.copy_bibtex)
        self.ui.About_CopyInfo.clicked.connect(self.copy_information)
        self.ui.About_RefreshInfo.clicked.connect(self.refresh_information)
        urls = dict(Website=WEBSITE, Documentation=DOCS, Repository=REPOSITORY,
                    Issues=REPOSITORY+'/issues', Updates=REPOSITORY+'/releases',
                    SoftwareLicence=SOURCE_ROOT+'LICENSE.txt',
                    HardwareLicence=SOURCE_ROOT+'Hardware/PCB/LICENSE')
        for key, url in urls.items():
            getattr(self.ui, 'About_' + key).clicked.connect(
                lambda checked=False, destination=url: self.open_url(destination))
        for key in ('Overview', 'Equations', 'Implementation', 'Limitations', 'References'):
            browser = getattr(self.ui, 'About_browser' + key)
            browser.setOpenLinks(False)
            browser.setOpenExternalLinks(False)
            browser.anchorClicked.connect(self._follow_link)
        for browser in (self.ui.About_referenceDetail, self.ui.About_scienceBrowser):
            browser.setOpenLinks(False)
            browser.setOpenExternalLinks(False)
            browser.anchorClicked.connect(self._follow_link)
        self.ui.About_articleTabs.currentChanged.connect(self._reading_changed)
        if self._manager is not None:
            self._manager.themeChanged.connect(self.apply_theme)
        serial_module = sys.modules.get('serial_manager')
        serial = getattr(serial_module, 'serial_manager', None)
        if serial is not None and hasattr(serial, 'connection_changed'):
            serial.connection_changed.connect(self.refresh_information)
        self.page.installEventFilter(self)
        self.retranslate()
        self.apply_theme()

    def eventFilter(self, watched, event):
        if watched is self.page and event.type() == QEvent.Type.LanguageChange:
            if not self._language_refresh_pending:
                self._language_refresh_pending = True
                QTimer.singleShot(0, self.retranslate)
        return super().eventFilter(watched, event)

    def retranslate(self):
        """Refresh literal UI strings and scientific text without changing location."""
        self._language_refresh_pending = False
        if not self._integrated:
            self.ui.retranslateUi(self.page)
        # Integrated static labels belong to UI_Spikeling and are translated
        # by the application. Do not overwrite edits made there in Designer.
        self._articles = {a['key']: a for a in articles()}
        self._populate_models()
        self._populate_references()
        self.ui.About_scienceBrowser.setHtml(science_text())
        self.ui.About_versionLabel.setText(QCoreApplication.translate('AboutPage', 'GUI {version}').format(version=app_version()))
        self.ui.About_statusLabel.clear()
        self._update_breadcrumb()
        self.refresh_information()

    def show(self):
        self.host.ui.mainbody_stackedWidget.setCurrentWidget(self.page)
        self.refresh_information()

    def select_section(self, index):
        self._section = index
        self.ui.About_stack.setCurrentIndex(index)
        self._buttons.button(index).setChecked(True)
        self.ui.About_statusLabel.clear()
        if index == 4:
            self.refresh_information()
        self._update_breadcrumb()

    def _update_breadcrumb(self):
        section = self._buttons.button(self._section).text().replace('&&', '&')
        path = QCoreApplication.translate('AboutPage', 'About') + ' / ' + section
        if self._section == 1:
            item = self.ui.About_modelList.currentItem()
            if item:
                path += ' / ' + item.text()
        self.ui.About_breadcrumbLabel.setText(path)

    def _populate_models(self, *_):
        query = self.ui.About_modelSearch.text().casefold().strip()
        view = self.ui.About_modelList
        view.blockSignals(True)
        view.clear()
        target = None
        for key, article in self._articles.items():
            haystack = ' '.join(str(article.get(k, '')) for k in ('title', 'overview', 'equations', 'implementation')).casefold()
            if query and query not in haystack:
                continue
            item = QListWidgetItem(article['title'])
            item.setData(Qt.ItemDataRole.UserRole, key)
            view.addItem(item)
            if key == self._topic:
                target = item
        view.setCurrentItem(target or view.item(0))
        view.blockSignals(False)
        self._topic_changed(view.currentItem(), None)

    def _topic_changed(self, current, previous):
        has_topic = current is not None
        self.ui.About_viewSource.setEnabled(has_topic)
        if not has_topic:
            self.ui.About_articleTitle.setText(QCoreApplication.translate('AboutPage', 'No matching models'))
            self.ui.About_provenanceLabel.clear()
            for key in ('Overview','Equations','Implementation','Limitations','References'):
                getattr(self.ui, 'About_browser'+key).clear()
            self._update_breadcrumb()
            return
        self._topic = current.data(Qt.ItemDataRole.UserRole)
        article = self._articles[self._topic]
        self.ui.About_articleTitle.setText(article['title'])
        self.ui.About_provenanceLabel.setText(article['provenance'])
        for key in ('overview', 'equations', 'implementation', 'limitations'):
            getattr(self.ui, 'About_browser' + key.capitalize()).setHtml(article[key])
        self.ui.About_browserReferences.setHtml(self._references_html(article))
        self._update_breadcrumb()

    def _references_html(self, article):
        labels = dict(adapted=QCoreApplication.translate('AboutPage', 'Adapted from'), inspired=QCoreApplication.translate('AboutPage', 'Inspired by'),
                      background=QCoreApplication.translate('AboutPage', 'Background reading'), implemented=QCoreApplication.translate('AboutPage', 'Implemented from'))
        parts = ['<h2>'+html.escape(QCoreApplication.translate('AboutPage', 'References & provenance'))+'</h2>']
        if not article['refs']:
            parts.append('<p>'+html.escape(QCoreApplication.translate('AboutPage', 'This note documents the project implementation. No additional primary-paper attribution is asserted here.'))+'</p>')
        for key, relation in article['refs']:
            parts.append('<p><b>'+html.escape(labels[relation])+'</b><br>'+html.escape(citation(key))+
                         '<br><a href="about-ref:'+key+'">'+html.escape(QCoreApplication.translate('AboutPage', 'View reference & copy citation'))+'</a></p>')
        parts.append('<p>'+html.escape(QCoreApplication.translate('AboutPage', 'Implementation notes reviewed against source revision:'))+' '+REVIEW_COMMIT+'</p>')
        return ''.join(parts)

    def show_topic(self, key):
        if key not in self._articles:
            return
        self._topic = key
        self.ui.About_modelSearch.clear()
        self._populate_models()
        self.ui.About_articleTabs.setCurrentIndex(0)
        self.select_section(1)

    def _reading_changed(self, index):
        # Keep the title/breadcrumb stable while switching scientific layers.
        self._update_breadcrumb()

    def _populate_references(self, *_):
        query = self.ui.About_referenceSearch.text().casefold().strip()
        view = self.ui.About_referenceList
        view.blockSignals(True)
        view.clear()
        target = None
        for key, ref in REFERENCES.items():
            if query and query not in citation(key).casefold():
                continue
            item = QListWidgetItem(ref['year']+' · '+ref['title'])
            item.setToolTip(citation(key))
            item.setData(Qt.ItemDataRole.UserRole, key)
            view.addItem(item)
            if key == self._reference:
                target = item
        view.setCurrentItem(target or view.item(0))
        view.blockSignals(False)
        self._reference_changed(view.currentItem(), None)

    def _reference_changed(self, current, previous):
        for key in ('OpenPaper', 'CopyCitation', 'CopyBibtex'):
            getattr(self.ui, 'About_' + key).setEnabled(current is not None)
        if current is None:
            self.ui.About_referenceDetail.setPlainText(QCoreApplication.translate('AboutPage', 'No matching references.'))
            return
        self._reference = current.data(Qt.ItemDataRole.UserRole)
        ref = REFERENCES[self._reference]
        uses = [article['title'] for article in self._articles.values()
                if any(key == self._reference for key, relation in article['refs'])]
        self.ui.About_referenceDetail.setHtml(
            '<h2>'+html.escape(ref['title'])+'</h2><p>'+html.escape(citation(self._reference))+'</p>'
            '<p><a href="https://doi.org/'+ref['doi']+'">'+html.escape(QCoreApplication.translate('AboutPage', 'Read publication'))+'</a></p>'
            '<h3>'+html.escape(QCoreApplication.translate('AboutPage', 'Related topics'))+'</h3><p>'+html.escape('; '.join(uses) or QCoreApplication.translate('AboutPage', 'The project'))+'</p>'
            '<p>'+html.escape(QCoreApplication.translate('AboutPage', 'See each topic for the relationship between the paper and the implementation.'))+'</p>')

    def show_reference(self, key):
        if key not in REFERENCES:
            return
        self._reference = key
        self.ui.About_referenceSearch.clear()
        self._populate_references()
        self.select_section(2)

    def _follow_link(self, url):
        if url.scheme() == 'about-ref':
            self.show_reference(url.path())
        else:
            self.open_url(url.toString())

    def open_url(self, url):
        """Open explicit HTTPS links in the system browser; never execute local URLs."""
        target = QUrl(url)
        if target.scheme() != 'https' or not target.host():
            self.ui.About_statusLabel.setText(QCoreApplication.translate('AboutPage', 'This link is not supported.'))
            return
        if not QDesktopServices.openUrl(target):
            self.ui.About_statusLabel.setText(QCoreApplication.translate('AboutPage', 'Could not open the browser.'))

    def view_source(self):
        if self.ui.About_modelList.currentItem() is not None:
            self.open_url(SOURCE_ROOT + quote(self._articles[self._topic]['source'], safe='/'))

    def open_paper(self):
        if self.ui.About_referenceList.currentItem() is not None:
            self.open_url('https://doi.org/' + REFERENCES[self._reference]['doi'])

    def _copy(self, text):
        QApplication.clipboard().setText(text)
        self.ui.About_statusLabel.setText(QCoreApplication.translate('AboutPage', 'Copied to clipboard.'))

    def copy_citation(self):
        if self.ui.About_referenceList.currentItem() is not None:
            self._copy(citation(self._reference))

    def copy_bibtex(self):
        if self.ui.About_referenceList.currentItem() is not None:
            self._copy(bibtex(self._reference))

    def refresh_information(self, *_):
        """Read existing state only. Never open/reset a device or probe its firmware."""
        unavailable = QCoreApplication.translate('AboutPage', 'Unavailable — not reported by the current connection')
        rows = [(QCoreApplication.translate('AboutPage', 'GUI version'), app_version()), (QCoreApplication.translate('AboutPage', 'Operating system'), platform.system()+' '+platform.release()),
                ('Python', platform.python_version()), ('PySide6', PySide6.__version__), ('Qt', qVersion())]
        for package in ('numpy', 'pyqtgraph', 'pandas'):
            try:
                value = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                value = QCoreApplication.translate('AboutPage', 'Version metadata unavailable')
            rows.append((package, value))
        serial_module = sys.modules.get('serial_manager')
        serial = getattr(serial_module, 'serial_manager', None)
        connected = serial is not None and serial.is_open
        rows.extend([(QCoreApplication.translate('AboutPage', 'Connection'), QCoreApplication.translate('AboutPage', 'Connected') if connected else QCoreApplication.translate('AboutPage', 'Not connected')),
                     (QCoreApplication.translate('AboutPage', 'Serial port'), str(serial.port_name) if connected else QCoreApplication.translate('AboutPage', 'None')),
                     (QCoreApplication.translate('AboutPage', 'Firmware version'), unavailable), (QCoreApplication.translate('AboutPage', 'Hardware revision'), unavailable),
                     (QCoreApplication.translate('AboutPage', 'Documentation source revision'), REVIEW_COMMIT)])
        report = '\n'.join(label+': '+value for label, value in rows)
        report += '\n\n' + QCoreApplication.translate('AboutPage', 'The documentation revision identifies the source reviewed for these notes. It is not a detected firmware version or a guarantee that the installed code is identical.')
        self.ui.About_diagnostics.setPlainText(report)

    def copy_information(self):
        self.refresh_information()
        self._copy(self.ui.About_diagnostics.toPlainText())

    def apply_theme(self, *_):
        """Style this page only, following the active Settings palette."""
        if self._manager is not None:
            colour = self._manager.active_colour
            window, panel, surface, text, muted, accent = [colour(key) for key in
                ('window_background','panel_background','surface','text_primary','text_muted','neuron_stimulus')]
        else:
            window, panel, surface, text, muted, accent = ('#001e26','#002b36','#073642','#becdcd','#839496','#2aa198')
        from PySide6.QtGui import QColor
        ac = QColor(accent)
        on_accent = '#001e26' if ac.lightnessF() > .55 else '#fdf6e3'
        self.page.setStyleSheet(f'''
          QWidget[aboutPanel="true"] {{background:{window};color:{text};font-size:10pt;}}
          QWidget[aboutPanel="true"] QScrollArea, QWidget#About_projectContents {{background:{window};border:0;}}
          QWidget[aboutPanel="true"] QCommandLinkButton {{font-size:12pt;text-align:left;}}
          QWidget[aboutPanel="true"] QLabel {{background:transparent;color:{text};}}
          QWidget[aboutPanel="true"] QGroupBox {{background:{panel};color:{text};border:1px solid {muted};border-radius:8px;margin-top:14px;padding:16px;}}
          QWidget[aboutPanel="true"] QGroupBox::title {{subcontrol-origin:margin;left:14px;padding:0 6px;color:{text};background:{panel};}}
          QWidget[aboutPanel="true"] QPushButton {{background:{surface};color:{text};border:1px solid {muted};border-radius:6px;padding:8px 12px;}}
          QWidget[aboutPanel="true"] QPushButton:hover {{border:1px solid {accent};}}
          QWidget[aboutPanel="true"] QPushButton:pressed, QWidget[aboutPanel="true"] QPushButton:checked {{background:{accent};color:{on_accent};}}
          QWidget[aboutPanel="true"] QPushButton:focus {{border:2px solid {accent};}}
          QWidget[aboutPanel="true"] QPushButton:disabled {{color:{muted};}}
          QWidget[aboutPanel="true"] QTextBrowser, QWidget[aboutPanel="true"] QPlainTextEdit,
          QWidget[aboutPanel="true"] QListWidget, QWidget[aboutPanel="true"] QLineEdit {{background:{panel};color:{text};border:1px solid {muted};border-radius:5px;padding:8px;selection-background-color:{accent};selection-color:{on_accent};}}
          QWidget[aboutPanel="true"] QListWidget::item {{padding:9px 5px;}}
          QWidget[aboutPanel="true"] QListWidget::item:selected {{background:{accent};color:{on_accent};}}
          QWidget[aboutPanel="true"] QScrollBar:vertical {{background:{panel};width:12px;}}
          QWidget[aboutPanel="true"] QScrollBar::handle:vertical {{background:{muted};min-height:24px;border-radius:5px;}}
          QWidget[aboutPanel="true"] QScrollBar::add-line:vertical, QWidget[aboutPanel="true"] QScrollBar::sub-line:vertical {{height:0;}}
          QWidget[aboutPanel="true"] QTabWidget::pane {{border:1px solid {muted};}}
          QWidget[aboutPanel="true"] QTabBar::tab {{background:{panel};color:{text};padding:9px 12px;border-bottom:2px solid {muted};}}
          QWidget[aboutPanel="true"] QTabBar::tab:selected {{border-bottom:2px solid {accent};background:{surface};}}
        ''')
        # A palette-coloured chevron remains visible in both dark and light modes.
        pixmap = QPixmap(22, 22)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(accent), 2.5))
        painter.drawLine(7, 4, 14, 11)
        painter.drawLine(14, 11, 7, 18)
        painter.end()
        for button in self.page.findChildren(QPushButton):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            if isinstance(button, QCommandLinkButton):
                button.setIcon(QIcon(pixmap))
        browsers = [getattr(self.ui,'About_browser'+key) for key in ('Overview','Equations','Implementation','Limitations','References')]
        browsers += [self.ui.About_referenceDetail, self.ui.About_scienceBrowser]
        for browser in browsers:
            palette = browser.palette()
            palette.setColor(QPalette.ColorRole.Text, QColor(text))
            palette.setColor(QPalette.ColorRole.Base, QColor(panel))
            palette.setColor(QPalette.ColorRole.Link, QColor(accent))
            browser.setPalette(palette)
            browser.document().setDefaultStyleSheet(f'body {{ color:{text}; font-size:11pt; }} a {{color:{accent};}} p {{margin-bottom:12px;}} h2 {{font-size:15pt;}}')
        # Existing documents also need re-rendering when HTML link colours change.
        self._topic_changed(self.ui.About_modelList.currentItem(), None)
        self._reference_changed(self.ui.About_referenceList.currentItem(), None)
        self.ui.About_scienceBrowser.setHtml(science_text())


def ShowPage(self):
    """Existing navigation entry point; construct once and reuse on later visits."""
    controller = getattr(self, '_about_page_controller', None)
    if controller is None:
        controller = AboutPage(self)
        self._about_page_controller = controller
    controller.show()
