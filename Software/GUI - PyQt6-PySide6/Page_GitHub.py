"""
GitHub page: version information and in-place application updates.

Shows the running version alongside the newest published release, and offers
a one-click download-and-install path that picks the archive matching the
host platform.

The controls are built programmatically inside ``page_901`` so the generated
``UI_Spikeling.py`` need not be regenerated, following the same pattern as
the Settings page.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QMessageBox, QProgressBar, QPushButton, QScrollArea, QSizePolicy,
    QSpacerItem, QTextBrowser, QVBoxLayout, QWidget,
)

from theme_manager import contrast_of, theme_manager
from update_installer import (
    InstallError, can_install, cleanup_staging, launch_installer, stage_update,
)
from update_service import (
    ReleaseInfo, UpdateService, UpdateStage, host_platform_key, install_root,
    is_frozen,
)
from version import __version__, GITHUB_OWNER, GITHUB_REPO, ISSUES_URL, RELEASES_URL, REPOSITORY_URL


ACTION_BUTTON_SIZE = (168, 34)
NOTES_MIN_HEIGHT = 220

PLATFORM_LABELS = {"Windows": "Windows", "Darwin": "macOS", "Linux": "Linux"}


class GitHubPage:
    """
    Controller for the GitHub / updates page.

    Parameters
    ----------
    parent : PySide6.QtWidgets.QMainWindow
        Main window owning ``self.ui``.
    service : update_service.UpdateService, optional
        Release client; a dedicated instance is created when omitted.
    """

    def __init__(self, parent, service: Optional[UpdateService] = None) -> None:
        self.parent = parent
        self.ui = parent.ui
        self.service = service or UpdateService(parent=parent)

        self._latest: Optional[ReleaseInfo] = None
        self._archive: Optional[Path] = None
        self._checked_once = False

        self._version_label: Optional[QLabel] = None
        self._latest_label: Optional[QLabel] = None
        self._status_label: Optional[QLabel] = None
        self._platform_label: Optional[QLabel] = None
        self._notes: Optional[QTextBrowser] = None
        self._progress: Optional[QProgressBar] = None
        self._check_button: Optional[QPushButton] = None
        self._install_button: Optional[QPushButton] = None
        self._prerelease_box: Optional[QCheckBox] = None

        self._build_controls()

        self.service.checkFinished.connect(self._on_check_finished)
        self.service.checkFailed.connect(self._on_check_failed)
        self.service.downloadProgress.connect(self._on_progress)
        self.service.downloadFinished.connect(self._on_download_finished)
        self.service.downloadFailed.connect(self._on_download_failed)
        self.service.stageChanged.connect(self._on_stage_changed)

        # An interrupted update leaves a partially extracted tree next to the
        # executable; clearing it here keeps the install directory tidy.
        cleanup_staging()

    # ------------------------------------------------------------------
    # Page selection
    # ------------------------------------------------------------------

    def ShowPage(self) -> None:
        """
        Display the page, checking for updates on the first visit.

        The check is deferred to first display rather than run at start-up:
        it must not add a network round trip to the launch path, and a user
        who never opens this page never contacts GitHub.
        """
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_801)
        if not self._checked_once:
            self._checked_once = True
            self.CheckForUpdates()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _build_controls(self) -> None:
        """Create the version and update widgets inside ``page_901``."""
        page = self.ui.page_801
        layout = page.layout()
        if layout is None:
            layout = QVBoxLayout(page)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(10)

        container = QWidget(page)
        container.setObjectName("GitHub_container")
        outer = QVBoxLayout(container)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(16)

        outer.addWidget(self._build_header(container))
        outer.addWidget(self._build_version_box(container))
        outer.addWidget(self._build_action_box(container))
        outer.addWidget(self._build_notes_box(container), stretch=1)
        outer.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Minimum))

        scroll = QScrollArea(page)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(container)
        layout.addWidget(scroll)

    @staticmethod
    def _make_group_box(parent: QWidget, title: str, name: str) -> QGroupBox:
        """Create a framed section box carrying the theming property."""
        box = QGroupBox(title, parent)
        box.setObjectName(name)
        box.setProperty("themeBox", "true")
        return box

    def _build_header(self, parent: QWidget) -> QWidget:
        """Build the title row and the repository link buttons."""
        frame = QFrame(parent)
        row = QHBoxLayout(frame)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        title = QLabel("Spikeling on GitHub", frame)
        title.setStyleSheet("font: 700 15pt; background: transparent;")
        row.addWidget(title)
        row.addStretch(1)

        for text, url in (("Repository", REPOSITORY_URL),
                          ("Releases", RELEASES_URL),
                          ("Report an issue", ISSUES_URL)):
            button = QPushButton(text, frame)
            button.setMinimumHeight(30)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda _=False, target=url: self._open(target))
            row.addWidget(button)

        return frame

    def _build_version_box(self, parent: QWidget) -> QGroupBox:
        """Build the installed / available version summary."""
        box = self._make_group_box(parent, "Version", "GitHub_Version_groupBox")
        grid = QGridLayout(box)
        grid.setContentsMargins(14, 18, 14, 14)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)

        mono = "font: 700 11pt 'Courier New'; background: transparent;"

        grid.addWidget(QLabel("Installed", box), 0, 0)
        self._version_label = QLabel(__version__, box)
        self._version_label.setStyleSheet(mono)
        grid.addWidget(self._version_label, 0, 1)

        grid.addWidget(QLabel("Latest release", box), 1, 0)
        self._latest_label = QLabel("Not checked yet", box)
        self._latest_label.setStyleSheet(mono)
        grid.addWidget(self._latest_label, 1, 1)

        grid.addWidget(QLabel("Platform", box), 2, 0)
        self._platform_label = QLabel(
            f"{PLATFORM_LABELS.get(host_platform_key(), host_platform_key())}"
            f"{'' if is_frozen() else '  (running from source)'}", box)
        grid.addWidget(self._platform_label, 2, 1)

        grid.addWidget(QLabel("Install location", box), 3, 0)
        location = QLabel(str(install_root()), box)
        location.setTextInteractionFlags(Qt.TextSelectableByMouse)
        location.setWordWrap(True)
        grid.addWidget(location, 3, 1)

        grid.setColumnStretch(1, 1)
        return box

    def _build_action_box(self, parent: QWidget) -> QGroupBox:
        """Build the check / install row, progress bar and status line."""
        box = self._make_group_box(parent, "Updates", "GitHub_Updates_groupBox")
        column = QVBoxLayout(box)
        column.setContentsMargins(14, 18, 14, 14)
        column.setSpacing(10)

        row = QHBoxLayout()
        row.setSpacing(10)

        self._check_button = self._make_button(box, "Check for updates",
                                               self.CheckForUpdates)
        self._install_button = self._make_button(box, "Download and install",
                                                 self.InstallUpdate)
        self._install_button.setEnabled(False)
        row.addWidget(self._check_button)
        row.addWidget(self._install_button)

        open_page = self._make_button(box, "Open release page",
                                      lambda: self._open(
                                          self._latest.url if self._latest
                                          else RELEASES_URL))
        row.addWidget(open_page)

        self._prerelease_box = QCheckBox("Include pre-releases", box)
        self._prerelease_box.setToolTip(
            "Release candidates and beta builds, tagged for example v2.1.0-rc.1")
        self._prerelease_box.toggled.connect(lambda _: self.CheckForUpdates())
        row.addWidget(self._prerelease_box)

        row.addStretch(1)
        column.addLayout(row)

        self._progress = QProgressBar(box)
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(True)
        self._progress.setVisible(False)
        column.addWidget(self._progress)

        self._status_label = QLabel("", box)
        self._status_label.setWordWrap(True)
        self._status_label.setStyleSheet("font: 700 9pt; background: transparent;")
        column.addWidget(self._status_label)

        return box

    def _build_notes_box(self, parent: QWidget) -> QGroupBox:
        """Build the release-notes viewer."""
        box = self._make_group_box(parent, "Release notes", "GitHub_Notes_groupBox")
        column = QVBoxLayout(box)
        column.setContentsMargins(14, 18, 14, 14)

        self._notes = QTextBrowser(box)
        self._notes.setOpenExternalLinks(True)
        self._notes.setMinimumHeight(NOTES_MIN_HEIGHT)
        self._notes.setPlaceholderText(
            "Release notes appear here after checking for updates.")
        column.addWidget(self._notes)

        return box

    @staticmethod
    def _make_button(parent: QWidget, text: str, slot) -> QPushButton:
        """Create one uniformly sized action button."""
        button = QPushButton(text, parent)
        button.setMinimumSize(*ACTION_BUTTON_SIZE)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(slot)
        return button

    @staticmethod
    def _open(url: str) -> None:
        """Open a URL in the system browser."""
        QDesktopServices.openUrl(QUrl(url))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def CheckForUpdates(self) -> None:
        """Query GitHub for the newest release."""
        self._set_status("Checking github.com for new releases...")
        self._install_button.setEnabled(False)
        self.service.check_for_updates(
            include_prereleases=self._prerelease_box.isChecked())

    def InstallUpdate(self) -> None:
        """Confirm, then download the archive for this platform."""
        if self._latest is None or self._latest.asset is None:
            return

        permitted, reason = can_install()
        if not permitted:
            QMessageBox.information(self.parent, "Cannot install automatically",
                                    f"{reason}\n\nThe release page will open so "
                                    f"the archive can be installed manually.")
            self._open(self._latest.url or RELEASES_URL)
            return

        size_mb = self._latest.asset.size / (1024 * 1024)
        answer = QMessageBox.question(
            self.parent, "Install update",
            f"Download {self._latest.asset.name} ({size_mb:.1f} MB) and install "
            f"it into:\n\n{install_root()}\n\n"
            f"Spikeling will close and reopen automatically. Recordings, "
            f"neurons and stimuli already on disk are preserved.\n\n"
            f"Stop any running acquisition before continuing.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if answer != QMessageBox.Yes:
            return

        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._set_status(f"Downloading {self._latest.asset.name}...")
        self.service.download(self._latest, install_root() / ".spikeling_update")

    # ------------------------------------------------------------------
    # Service callbacks
    # ------------------------------------------------------------------

    def _on_check_finished(self, release: Optional[ReleaseInfo]) -> None:
        """Present the newest release, or report that none was found."""
        self._latest = release

        if release is None:
            self._latest_label.setText("None found")
            self._set_status("No published release matched the current filter.")
            return

        suffix = "  (pre-release)" if release.prerelease else ""
        self._latest_label.setText(f"{release.tag}{suffix}")
        self._notes.setMarkdown(release.notes or "_No release notes provided._")

        if not release.is_newer_than_running:
            self._install_button.setEnabled(False)
            self._set_status(f"Spikeling {__version__} is up to date.", good=True)
            return

        if release.asset is None:
            self._install_button.setEnabled(False)
            platform_name = PLATFORM_LABELS.get(host_platform_key(), host_platform_key())
            self._set_status(
                f"{release.tag} is available but publishes no {platform_name} "
                f"build. Open the release page to check manually.")
            return

        permitted, reason = can_install()
        self._install_button.setEnabled(permitted)
        size_mb = release.asset.size / (1024 * 1024)
        self._set_status(
            f"{release.tag} is available ({release.asset.name}, {size_mb:.1f} MB)."
            + ("" if permitted else f"  {reason}"), attention=True)

    def _on_check_failed(self, reason: str) -> None:
        """Report a failed release query."""
        self._latest_label.setText("Check failed")
        self._set_status(reason, bad=True)

    def _on_progress(self, received: int, total: int) -> None:
        """Update the download progress bar."""
        if total <= 0:
            self._progress.setRange(0, 0)       # indeterminate
            return
        self._progress.setRange(0, 100)
        self._progress.setValue(int(received * 100 / total))
        self._progress.setFormat(
            f"{received / (1024 * 1024):.1f} / {total / (1024 * 1024):.1f} MB  (%p%)")

    def _on_download_finished(self, path: str) -> None:
        """Stage the archive and hand over to the external installer."""
        self._archive = Path(path)
        self._progress.setVisible(False)
        self._set_status("Download verified. Preparing installation...")

        try:
            plan = stage_update(self._archive)
        except (InstallError, OSError) as error:
            self._set_status(f"Installation could not be prepared: {error}", bad=True)
            QMessageBox.warning(self.parent, "Update failed", str(error))
            return

        if plan.preserved:
            print(f"Update: preserved {len(plan.preserved)} existing user files.")

        try:
            launch_installer(plan)
        except InstallError as error:
            self._set_status(str(error), bad=True)
            QMessageBox.warning(self.parent, "Update failed", str(error))
            return

        QMessageBox.information(
            self.parent, "Restarting",
            "Spikeling will now close and reopen on the new version.\n\n"
            "If it does not reappear within a few seconds, launch it manually "
            f"from:\n{install_root()}")

        QApplication.instance().quit()

    def _on_download_failed(self, reason: str) -> None:
        """Report a failed download."""
        self._progress.setVisible(False)
        self._set_status(reason, bad=True)

    def _on_stage_changed(self, stage: UpdateStage) -> None:
        """Disable the controls while a request is in flight."""
        busy = stage in (UpdateStage.CHECKING, UpdateStage.DOWNLOADING,
                         UpdateStage.VERIFYING)
        self._check_button.setEnabled(not busy)
        self._prerelease_box.setEnabled(not busy)
        if busy:
            self._install_button.setEnabled(False)

    # ------------------------------------------------------------------
    # Status line
    # ------------------------------------------------------------------

    def _set_status(self, text: str, good: bool = False, bad: bool = False,
                    attention: bool = False) -> None:
        """
        Write the status line, tinted from the active theme.

        Colours are pulled from the theme rather than hard-coded so the line
        stays legible in both light and dark modes.
        """
        if self._status_label is None:
            return

        if bad:
            colour = theme_manager.active_colour("neuron_vm")
        elif good:
            colour = theme_manager.active_colour("neuron_current")
        elif attention:
            colour = theme_manager.active_colour("neuron_stimulus")
        else:
            colour = theme_manager.active_colour("text_primary")

        self._status_label.setStyleSheet(
            f"color: {colour}; font: 700 9pt; background: transparent;")
        self._status_label.setText(text)


def ShowPage(self) -> None:
    """Display the GitHub page from a ``MainWindow`` instance."""
    page = getattr(self, "github_page", None)
    if page is not None:
        page.ShowPage()
    else:
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_901)
