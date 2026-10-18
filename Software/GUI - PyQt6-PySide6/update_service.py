"""
Release discovery and download for the Spikeling GUI.

Queries the GitHub REST API for published releases, selects the asset
matching the host platform, and downloads it with progress reporting and
SHA-256 verification.

Networking uses :mod:`PySide6.QtNetwork` rather than ``urllib`` in a worker
thread: it is already a dependency, it is non-blocking on the Qt event loop
by construction, and it avoids the certificate-store differences between
CPython's ``ssl`` module on the three platforms.

Build requirement
-----------------
Qt resolves TLS through a plugin (``plugins/tls``). PyInstaller specs that
collect only ``platforms`` and ``imageformats`` produce a binary where every
HTTPS request fails with ``UnknownNetworkError`` and no further diagnostic.
See the spec changes shipped alongside this module.
"""

from __future__ import annotations

import hashlib
import platform
import re
import sys
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from PySide6.QtCore import QByteArray, QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from version import GITHUB_OWNER, GITHUB_REPO, __version__

import json


API_ROOT = "https://api.github.com"
USER_AGENT = f"Spikeling-GUI/{__version__.lstrip('v')}"

#: GitHub rejects unauthenticated API calls without a User-Agent, and serves
#: a stable schema only when the version media type is requested explicitly.
API_HEADERS = {
    b"User-Agent": USER_AGENT.encode(),
    b"Accept": b"application/vnd.github+json",
    b"X-GitHub-Api-Version": b"2022-11-28",
}

#: Token substrings identifying the platform an asset was built for, in the
#: naming scheme used by the release workflow (``Spikeling-v1.2.3-Linux.zip``).
PLATFORM_TOKENS = {
    "Windows": ("windows", "win"),
    "Darwin": ("macos", "darwin", "osx", "mac"),
    "Linux": ("linux",),
}

CHECKSUM_ASSET_NAMES = ("SHA256SUMS.txt", "SHA256SUMS")

DOWNLOAD_CHUNK_LOG_BYTES = 256 * 1024


# =============================================================================
# Version ordering
# =============================================================================

_VERSION_PATTERN = re.compile(
    r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[-+](.*))?$", re.IGNORECASE
)


def parse_version(tag: str) -> Optional[Tuple[int, int, int, Tuple]]:
    """
    Parse a release tag into a sortable key.

    Pre-release ordering follows semantic versioning: a tag carrying a
    suffix precedes the same numeric version without one, so ``v2.1.0-rc.1``
    sorts below ``v2.1.0``. Suffix components compare numerically when both
    are numeric and lexically otherwise, which orders ``rc.2`` after ``rc.1``
    rather than treating ``10`` as smaller than ``9``.

    Parameters
    ----------
    tag : str
        Git tag, with or without a leading ``v``.

    Returns
    -------
    tuple or None
        ``(major, minor, patch, suffix_key)``, or ``None`` when the tag does
        not look like a version at all.
    """
    match = _VERSION_PATTERN.match(str(tag).strip())
    if match is None:
        return None

    major, minor, patch, suffix = match.groups()
    numbers = (int(major), int(minor or 0), int(patch or 0))

    if not suffix:
        # Empty tuple sorts after any populated one at equal numbers, which
        # is exactly the "release outranks its candidates" rule.
        return numbers + ((1,),)

    parts: List = [0]
    for chunk in re.split(r"[.\-+]", suffix):
        if not chunk:
            continue
        parts.append((0, int(chunk)) if chunk.isdigit() else (1, chunk.lower()))
    return numbers + (tuple(parts),)


def is_newer(candidate: str, current: str) -> bool:
    """
    Return ``True`` when ``candidate`` is a strictly later version.

    An unparseable current version is treated as "older than everything", so
    a locally modified build still sees updates rather than silently
    refusing them.
    """
    candidate_key = parse_version(candidate)
    if candidate_key is None:
        return False
    current_key = parse_version(current)
    return current_key is None or candidate_key > current_key


# =============================================================================
# Release model
# =============================================================================

def host_platform_key() -> str:
    """Return ``'Windows'``, ``'Darwin'`` or ``'Linux'`` for this host."""
    return platform.system()


def is_frozen() -> bool:
    """Return ``True`` when running from a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False))


def install_root() -> Path:
    """
    Return the directory an update would be written into.

    Frozen builds resolve to the folder holding the executable, which is
    where the release archive also places ``Recordings``, ``Neurons`` and
    ``Stimuli``. Source checkouts resolve to the module directory, which the
    installer refuses to touch.
    """
    base = Path(sys.executable if is_frozen() else __file__).resolve()
    return base.parent


@dataclass(frozen=True)
class ReleaseAsset:
    """
    One downloadable file attached to a release.

    Attributes
    ----------
    name : str
        File name as published.
    url : str
        Browser download URL; GitHub redirects it to object storage.
    size : int
        Size in bytes, used for the progress bar and a sanity check.
    """

    name: str
    url: str
    size: int


@dataclass(frozen=True)
class ReleaseInfo:
    """
    A published release and the asset matching this host.

    Attributes
    ----------
    tag : str
        Git tag, for example ``v2.1.0``.
    title : str
        Release title, falling back to the tag when blank.
    notes : str
        Markdown release body.
    url : str
        Public release page.
    published_at : str
        ISO-8601 publication timestamp.
    prerelease : bool
        Whether GitHub flagged this as a pre-release.
    asset : ReleaseAsset or None
        Archive for the host platform, ``None`` when the release carries no
        build for it.
    checksums : ReleaseAsset or None
        ``SHA256SUMS`` asset when the release publishes one.
    """

    tag: str
    title: str
    notes: str
    url: str
    published_at: str
    prerelease: bool
    asset: Optional[ReleaseAsset]
    checksums: Optional[ReleaseAsset]

    @property
    def is_newer_than_running(self) -> bool:
        """Whether this release supersedes the running build."""
        return is_newer(self.tag, __version__)


def _select_platform_asset(assets: Iterable[dict]) -> Optional[ReleaseAsset]:
    """Pick the archive built for the host platform, if present."""
    tokens = PLATFORM_TOKENS.get(host_platform_key(), ())
    for entry in assets:
        name = str(entry.get("name", ""))
        lowered = name.lower()
        if lowered.endswith(".zip") and any(token in lowered for token in tokens):
            return ReleaseAsset(name, str(entry.get("browser_download_url", "")),
                                int(entry.get("size", 0)))
    return None


def _select_checksum_asset(assets: Iterable[dict]) -> Optional[ReleaseAsset]:
    """Pick the published checksum manifest, if any."""
    for entry in assets:
        if str(entry.get("name", "")) in CHECKSUM_ASSET_NAMES:
            return ReleaseAsset(str(entry["name"]),
                                str(entry.get("browser_download_url", "")),
                                int(entry.get("size", 0)))
    return None


def release_from_payload(payload: dict) -> ReleaseInfo:
    """Build a :class:`ReleaseInfo` from one GitHub API release object."""
    assets = payload.get("assets") or []
    tag = str(payload.get("tag_name", ""))
    return ReleaseInfo(
        tag=tag,
        title=str(payload.get("name") or tag),
        notes=str(payload.get("body") or ""),
        url=str(payload.get("html_url", "")),
        published_at=str(payload.get("published_at", "")),
        prerelease=bool(payload.get("prerelease", False)),
        asset=_select_platform_asset(assets),
        checksums=_select_checksum_asset(assets),
    )


# =============================================================================
# Service
# =============================================================================

class UpdateStage(Enum):
    """Lifecycle of an update operation, for status reporting."""

    IDLE = auto()
    CHECKING = auto()
    DOWNLOADING = auto()
    VERIFYING = auto()
    READY = auto()
    FAILED = auto()


class UpdateService(QObject):
    """
    Query GitHub for releases and download the archive for this platform.

    Parameters
    ----------
    owner, repo : str, optional
        Repository to query; defaults to the values in :mod:`version`.
    parent : PySide6.QtCore.QObject, optional
        Qt parent.

    Attributes
    ----------
    checkFinished : Signal(object)
        Emitted with the newest :class:`ReleaseInfo`, or ``None`` when the
        repository publishes nothing usable.
    checkFailed : Signal(str)
        Emitted with a user-facing reason when the query fails.
    downloadProgress : Signal(int, int)
        ``(received, total)`` in bytes; ``total`` is ``-1`` while unknown.
    downloadFinished : Signal(str)
        Emitted with the path of the verified archive.
    downloadFailed : Signal(str)
        Emitted with a user-facing reason when the download fails.
    stageChanged : Signal(object)
        Emitted on every :class:`UpdateStage` transition.
    """

    checkFinished = Signal(object)
    checkFailed = Signal(str)
    downloadProgress = Signal(int, int)
    downloadFinished = Signal(str)
    downloadFailed = Signal(str)
    stageChanged = Signal(object)

    def __init__(self, owner: str = GITHUB_OWNER, repo: str = GITHUB_REPO,
                 parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._owner = owner
        self._repo = repo
        self._network = QNetworkAccessManager(self)
        self._stage = UpdateStage.IDLE

        self._reply: Optional[QNetworkReply] = None
        self._destination: Optional[Path] = None
        self._handle = None
        self._digest = None
        self._expected_sha256: Optional[str] = None
        self._pending_release: Optional[ReleaseInfo] = None

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def stage(self) -> UpdateStage:
        """Current lifecycle stage."""
        return self._stage

    @property
    def busy(self) -> bool:
        """Whether a request is in flight."""
        return self._stage in (UpdateStage.CHECKING, UpdateStage.DOWNLOADING,
                               UpdateStage.VERIFYING)

    def _set_stage(self, stage: UpdateStage) -> None:
        if stage is not self._stage:
            self._stage = stage
            self.stageChanged.emit(stage)

    def _request(self, url: str) -> QNetworkRequest:
        """Build a request carrying the mandatory GitHub headers."""
        request = QNetworkRequest(QUrl(url))
        for header, value in API_HEADERS.items():
            request.setRawHeader(QByteArray(header), QByteArray(value))
        request.setAttribute(QNetworkRequest.RedirectPolicyAttribute,
                             QNetworkRequest.NoLessSafeRedirectPolicy)
        return request

    # ------------------------------------------------------------------
    # Release query
    # ------------------------------------------------------------------

    def check_for_updates(self, include_prereleases: bool = False) -> None:
        """
        Fetch the release list and report the newest usable entry.

        Parameters
        ----------
        include_prereleases : bool, optional
            Consider releases GitHub flagged as pre-release. The full list
            endpoint is used rather than ``/releases/latest`` because the
            latter omits pre-releases unconditionally and also omits any
            release not marked *latest*, which a pre-release never is.
        """
        if self.busy:
            return

        self._set_stage(UpdateStage.CHECKING)
        url = f"{API_ROOT}/repos/{self._owner}/{self._repo}/releases?per_page=30"
        reply = self._network.get(self._request(url))
        reply.finished.connect(lambda: self._on_check_finished(reply, include_prereleases))

    def _on_check_finished(self, reply: QNetworkReply, include_prereleases: bool) -> None:
        """Parse the release list and emit the newest candidate."""
        reply.deleteLater()

        if reply.error() != QNetworkReply.NoError:
            self._set_stage(UpdateStage.FAILED)
            self.checkFailed.emit(self._describe_error(reply))
            return

        try:
            payload = json.loads(bytes(reply.readAll().data()).decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as error:
            self._set_stage(UpdateStage.FAILED)
            self.checkFailed.emit(f"Malformed response from GitHub: {error}")
            return

        if not isinstance(payload, list):
            self._set_stage(UpdateStage.FAILED)
            self.checkFailed.emit("Unexpected response from GitHub.")
            return

        releases = [
            release_from_payload(entry) for entry in payload
            if not entry.get("draft", False)
        ]
        if not include_prereleases:
            releases = [r for r in releases if not r.prerelease]

        ranked = sorted(
            (r for r in releases if parse_version(r.tag) is not None),
            key=lambda r: parse_version(r.tag),
            reverse=True,
        )

        self._set_stage(UpdateStage.IDLE)
        self.checkFinished.emit(ranked[0] if ranked else None)

    @staticmethod
    def _describe_error(reply: QNetworkReply) -> str:
        """Turn a Qt network failure into an actionable message."""
        status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)

        if status == 403:
            return ("GitHub rate limit reached for this network. "
                    "Try again in an hour, or open the releases page manually.")
        if status == 404:
            return "Repository or release not found. Check the configured repository."
        if reply.error() in (QNetworkReply.HostNotFoundError,
                             QNetworkReply.UnknownNetworkError,
                             QNetworkReply.NetworkSessionFailedError):
            return ("Could not reach github.com. Check the network connection, "
                    "or a proxy if this machine sits behind one.")
        if reply.error() in (QNetworkReply.SslHandshakeFailedError,
                             QNetworkReply.UnknownServerError):
            return ("Secure connection failed. This build may be missing its Qt "
                    "TLS plugin; please report it with your platform.")
        return reply.errorString() or "Unknown network error."

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download(self, release: ReleaseInfo, destination_dir: Path) -> None:
        """
        Download the platform archive, verifying it when possible.

        The checksum manifest is fetched first when the release publishes
        one, so a truncated or tampered archive is rejected before anything
        is written over an installed application.

        Parameters
        ----------
        release : ReleaseInfo
            Release to fetch; must carry a platform asset.
        destination_dir : pathlib.Path
            Directory the archive is written into; created if absent.
        """
        if self.busy or release.asset is None:
            return

        destination_dir.mkdir(parents=True, exist_ok=True)
        self._pending_release = release
        self._destination = destination_dir / release.asset.name
        self._expected_sha256 = None

        if release.checksums is not None:
            self._set_stage(UpdateStage.VERIFYING)
            reply = self._network.get(self._request(release.checksums.url))
            reply.finished.connect(lambda: self._on_checksums_fetched(reply))
            return

        self._start_asset_download()

    def _on_checksums_fetched(self, reply: QNetworkReply) -> None:
        """Record the expected digest, then start the archive download."""
        reply.deleteLater()

        if reply.error() == QNetworkReply.NoError and self._pending_release is not None:
            text = bytes(reply.readAll().data()).decode("utf-8", errors="replace")
            wanted = self._pending_release.asset.name
            for line in text.splitlines():
                parts = line.split()
                if len(parts) >= 2 and Path(parts[-1]).name == wanted:
                    self._expected_sha256 = parts[0].lower()
                    break

        self._start_asset_download()

    def _start_asset_download(self) -> None:
        """Open the destination file and begin streaming the asset."""
        release = self._pending_release
        if release is None or release.asset is None or self._destination is None:
            return

        try:
            self._handle = open(self._destination, "wb")
        except OSError as error:
            self._fail_download(f"Cannot write to {self._destination.parent}: {error}")
            return

        self._digest = hashlib.sha256()
        self._set_stage(UpdateStage.DOWNLOADING)

        reply = self._network.get(self._request(release.asset.url))
        self._reply = reply
        # Streamed to disk as it arrives: a 150 MB archive held in memory
        # would be a needless spike on the machines this runs on.
        reply.readyRead.connect(lambda: self._on_chunk(reply))
        reply.downloadProgress.connect(self.downloadProgress)
        reply.finished.connect(lambda: self._on_download_finished(reply))

    def _on_chunk(self, reply: QNetworkReply) -> None:
        """Append one received chunk to the file and the running digest."""
        if self._handle is None:
            return
        chunk = bytes(reply.readAll().data())
        self._handle.write(chunk)
        self._digest.update(chunk)

    def _on_download_finished(self, reply: QNetworkReply) -> None:
        """Close the file, verify the digest and report the outcome."""
        reply.deleteLater()
        self._reply = None

        if self._handle is not None:
            self._handle.close()
            self._handle = None

        if reply.error() != QNetworkReply.NoError:
            self._fail_download(self._describe_error(reply))
            return

        path = self._destination
        release = self._pending_release
        if path is None or release is None:
            self._fail_download("Download completed with no destination recorded.")
            return

        actual = self._digest.hexdigest() if self._digest else ""
        if self._expected_sha256 and actual != self._expected_sha256:
            path.unlink(missing_ok=True)
            self._fail_download(
                "Checksum mismatch: the download is corrupt and was discarded.")
            return

        expected_size = release.asset.size
        if expected_size and path.stat().st_size != expected_size:
            path.unlink(missing_ok=True)
            self._fail_download("Download is incomplete and was discarded.")
            return

        self._set_stage(UpdateStage.READY)
        self.downloadFinished.emit(str(path))

    def _fail_download(self, reason: str) -> None:
        """Abandon the download and report a reason."""
        if self._handle is not None:
            self._handle.close()
            self._handle = None
        self._set_stage(UpdateStage.FAILED)
        self.downloadFailed.emit(reason)

    def cancel(self) -> None:
        """Abort any transfer in flight and discard the partial file."""
        if self._reply is not None:
            self._reply.abort()
            self._reply = None
        if self._handle is not None:
            self._handle.close()
            self._handle = None
        if self._destination is not None:
            Path(self._destination).unlink(missing_ok=True)
        self._set_stage(UpdateStage.IDLE)
