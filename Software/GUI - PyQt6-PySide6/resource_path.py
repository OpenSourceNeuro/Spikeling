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


def application_resource_root() -> Path:
    """
    Return the directory holding bundled resources.

    Returns
    -------
    pathlib.Path
        ``sys._MEIPASS`` inside a PyInstaller bundle, otherwise the directory
        containing this module.
    """
    bundle_directory = getattr(sys, "_MEIPASS", None)
    return Path(bundle_directory) if bundle_directory else Path(__file__).resolve().parent


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
