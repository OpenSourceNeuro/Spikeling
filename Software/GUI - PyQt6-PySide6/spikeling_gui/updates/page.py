"""
GitHub page: version information and in-place application updates.

Shows the running version alongside the newest published release, and offers
a one-click download-and-install path that picks the archive matching the
host platform.

The page layout and static text live in UI_Spikeling.ui. This controller
binds the Designer widgets to the release service and the project links.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMessageBox

from spikeling_gui.appearance.dialogs import themed_message_box
from spikeling_gui.appearance.theme_manager import theme_manager
from .installer import InstallError, can_install, cleanup_staging, launch_installer, stage_update
from .service import ReleaseInfo, UpdateService, UpdateStage, host_platform_key, install_root, is_frozen
from spikeling_gui.version import __version__, ISSUES_URL, RELEASES_URL, REPOSITORY_URL


DOCUMENTATION_URL = "https://opensourceneuro.github.io/Spikeling/"
PROJECT_PAPER_URL = "https://doi.org/10.1371/journal.pbio.2006760"

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

        self._bind_controls()

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
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_GitHub)
        if not self._checked_once:
            self._checked_once = True
            self.CheckForUpdates()

    # ------------------------------------------------------------------
    # Designer bindings
    # ------------------------------------------------------------------

    def _bind_controls(self) -> None:
        ui = self.ui
        self._latest_label = ui.GitHub_LatestValue_label
        self._status_label = ui.GitHub_Status_label
        self._notes = ui.GitHub_Notes_textBrowser
        self._progress = ui.GitHub_Download_progressBar
        self._check_button = ui.GitHub_Check_pushButton
        self._install_button = ui.GitHub_Install_pushButton
        self._prerelease_box = ui.GitHub_Prereleases_checkBox

        platform = host_platform_key()
        platform_name = PLATFORM_LABELS.get(platform, platform)
        ui.GitHub_InstalledValue_label.setText(__version__)
        ui.GitHub_PlatformValue_label.setText(platform_name)
        if not is_frozen():
            ui.GitHub_PlatformValue_label.setText(
                self.parent.tr("%1 (running from source)").replace("%1", platform_name))
        ui.GitHub_InstallPathValue_label.setText(str(install_root()))
        self._progress.hide()

        self._check_button.clicked.connect(self.CheckForUpdates)
        self._install_button.clicked.connect(self.InstallUpdate)
        self._prerelease_box.toggled.connect(lambda _: self.CheckForUpdates())
        ui.GitHub_OpenRelease_pushButton.clicked.connect(
            lambda: self._open(self._latest.url if self._latest and self._latest.url
                               else RELEASES_URL))

        links = (
            (ui.GitHub_Repository_pushButton, REPOSITORY_URL),
            (ui.GitHub_Documentation_pushButton, DOCUMENTATION_URL),
            (ui.GitHub_Issues_pushButton, ISSUES_URL),
            (ui.GitHub_Contribute_pushButton, f"{REPOSITORY_URL}#contributing"),
        )
        for button, url in links:
            button.clicked.connect(lambda checked=False, target=url: self._open(target))

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
            themed_message_box(
                self.parent, "Cannot install automatically",
                f"{reason}\n\nThe release page will open so "
                "the archive can be installed manually.",
                QMessageBox.Icon.Information,
            ).exec()
            self._open(self._latest.url or RELEASES_URL)
            return

        size_mb = self._latest.asset.size / (1024 * 1024)
        box = themed_message_box(
            self.parent, "Install update",
            f"Download {self._latest.asset.name} ({size_mb:.1f} MB) and install "
            f"it into:\n\n{install_root()}\n\n"
            f"Spikeling will close and reopen automatically. Recordings, "
            f"neurons and stimuli already on disk are preserved.\n\n"
            f"Stop any running acquisition before continuing.",
            QMessageBox.Icon.Question,
        )
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)

        if box.exec() != QMessageBox.StandardButton.Yes.value:
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
            themed_message_box(self.parent, "Update failed", str(error)).exec()
            return

        if plan.preserved:
            print(f"Update: preserved {len(plan.preserved)} existing user files.")

        try:
            launch_installer(plan)
        except InstallError as error:
            self._set_status(str(error), bad=True)
            themed_message_box(self.parent, "Update failed", str(error)).exec()
            return

        themed_message_box(
            self.parent, "Restarting",
            "Spikeling will now close and reopen on the new version.\n\n"
            "If it does not reappear within a few seconds, launch it manually "
            f"from:\n{install_root()}",
            QMessageBox.Icon.Information,
        ).exec()

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
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_GitHub)
