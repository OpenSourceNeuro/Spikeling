"""
Filesystem resolution of bundled application assets.

PyInstaller unpacks a one-file build into a temporary directory exposed as
``sys._MEIPASS``, while the process working directory remains wherever the
user launched the executable from. An asset addressed by a bare relative path
(``"resources/Spiky1.png"``) therefore resolves when running from source and
silently fails once frozen: ``QPixmap`` returns a null pixmap and the caller
falls back to a placeholder.

Every asset lookup in the project must go through :func:`resource_path` so
that source runs and frozen builds share one resolution rule.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QPixmap


def source_gui_directory() -> Path:
    """Return the source GUI directory containing Main.py."""
    return Path(__file__).resolve().parent.parent


def application_resource_root() -> Path:
    """Return the directory containing loose application assets."""
    bundle_directory = getattr(sys, "_MEIPASS", None)
    if bundle_directory is not None:
        return Path(bundle_directory)
    return source_gui_directory()

def application_directory() -> Path:
    """Return the directory containing Main.py or the packaged executable."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return source_gui_directory()


def data_directory(kind: str) -> Path:
    """Return a folder within the portable Spikeling data directory."""
    return application_directory() / "Data" / kind


def resource_path(*parts: str | Path) -> Path:
    """
    Resolve an asset path against the application resource root.

    Parameters
    ----------
    *parts : str or pathlib.Path
        Path fragments relative to the resource root, e.g.
        ``("resources", "geci", "GCaMP6s")``. An absolute first fragment is
        returned unchanged, so already-resolved paths pass through safely.

    Returns
    -------
    pathlib.Path
        Absolute path to the asset, which may or may not exist.

    Examples
    --------
    >>> resource_path("resources", "Spiky1.png").name
    'Spiky1.png'
    """
    candidate = Path(*parts)
    return candidate if candidate.is_absolute() else application_resource_root() / candidate


def recordings_directory() -> Path:
    """Return the shared destination for all recording modes."""
    return data_directory("Recordings")


def save_dialog_directory(directory: Path) -> str:
    """Prepare a starting folder for a save or folder-selection dialog."""
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        return ""  # Let Qt open the dialog so the user can choose another folder.
    return str(directory)

def load_pixmap(*parts: str | Path, warn: bool = True) -> QPixmap:
    """
    Load a bundled image, reporting a missing or undecodable file.

    A null :class:`~PySide6.QtGui.QPixmap` is indistinguishable from a
    deliberately empty one at the call site, which is how a packaging error
    previously surfaced as a silent cosmetic downgrade rather than as an
    error. The warning makes the failure visible in the console.

    Parameters
    ----------
    *parts : str or pathlib.Path
        Fragments forwarded to :func:`resource_path`.
    warn : bool, optional
        Print a diagnostic when the pixmap cannot be loaded.

    Returns
    -------
    PySide6.QtGui.QPixmap
        The decoded image, or a null pixmap on failure.
    """
    path = resource_path(*parts)
    pixmap = QPixmap(str(path))
    if pixmap.isNull() and warn:
        print(f"[resources] missing or undecodable asset: {path}")
    return pixmap
