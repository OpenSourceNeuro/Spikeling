"""
In-place installation of a downloaded Spikeling release.

A running executable cannot replace itself: Windows holds an exclusive lock
on it, and on POSIX the kernel keeps the original inode mapped even after an
unlink. The update is therefore applied by an external helper script that
waits for this process to exit, swaps the files, and relaunches.

Division of labour
------------------
Everything that benefits from being testable happens in Python: archive
extraction, path validation, and pruning of files that must not overwrite
user data. The generated shell script is deliberately trivial, because a bug
in it surfaces only on the user's machine, after the application has already
quit.

Safety properties
-----------------
* Archive members are validated against directory traversal before extraction.
* The previous executable is kept as ``.backup`` and restored if the new one
  is missing after the swap.
* ``Recordings``, ``Neurons`` and ``Stimuli`` are merged, never replaced: a
  file already present on disk is pruned from the payload, so a user's
  recordings survive the update.
* Installation is refused outright when the target directory is not writable,
  rather than half-applied.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from update_service import host_platform_key, install_root, is_frozen


STAGING_DIRNAME = ".spikeling_update"
PAYLOAD_DIRNAME = "payload"
BACKUP_SUFFIX = ".backup"

#: Directories shipped in the archive that hold user data after first launch.
#: Members already present on disk are dropped from the payload.
USER_DATA_DIRS = ("Recordings", "Neurons", "Stimuli")

#: Seconds the helper waits for this process to exit before giving up.
EXIT_TIMEOUT_SECONDS = 60


class InstallError(RuntimeError):
    """Raised when an update cannot be staged or launched."""


@dataclass(frozen=True)
class InstallPlan:
    """
    A staged, ready-to-apply update.

    Attributes
    ----------
    payload_dir : pathlib.Path
        Extracted tree whose contents are copied over the install root.
    install_dir : pathlib.Path
        Destination directory.
    executable_name : str
        Name of the application binary inside the payload.
    staging_dir : pathlib.Path
        Parent scratch directory, removed by the helper when it finishes.
    preserved : tuple of str
        User files that were pruned from the payload.
    """

    payload_dir: Path
    install_dir: Path
    executable_name: str
    staging_dir: Path
    preserved: tuple


def executable_name() -> str:
    """Return the application binary name for this platform."""
    return "Spikeling.exe" if host_platform_key() == "Windows" else "Spikeling"


def can_install(target: Optional[Path] = None) -> tuple:
    """
    Report whether an in-place update is possible.

    Parameters
    ----------
    target : pathlib.Path, optional
        Directory to test; defaults to the install root.

    Returns
    -------
    (bool, str)
        Whether installation may proceed, and an explanatory reason when it
        may not.
    """
    if not is_frozen():
        return False, ("Running from source: update the working copy with git "
                       "instead of installing a release archive.")

    directory = Path(target or install_root())
    if not directory.is_dir():
        return False, f"Install directory does not exist: {directory}"
    if not os.access(directory, os.W_OK | os.X_OK):
        return False, (f"No write permission for {directory}. Move the "
                       f"application to a writable location, or download the "
                       f"release manually.")
    return True, ""


def _is_within(base: Path, candidate: Path) -> bool:
    """Return ``True`` when ``candidate`` resolves inside ``base``."""
    try:
        candidate.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _safe_extract(archive: Path, destination: Path) -> None:
    """
    Extract a zip, rejecting traversal and restoring Unix permissions.

    :mod:`zipfile` discards the mode bits stored in ``external_attr``, so a
    binary extracted with it is not executable. The bits are re-applied here;
    without this the updated application cannot be launched on Linux or
    macOS.

    Parameters
    ----------
    archive : pathlib.Path
        Downloaded ``.zip``.
    destination : pathlib.Path
        Empty directory to populate.

    Raises
    ------
    InstallError
        If a member would escape ``destination``.
    """
    destination.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            target = destination / member.filename
            if not _is_within(destination, target):
                raise InstallError(
                    f"Archive contains an unsafe path and was rejected: "
                    f"{member.filename}")

            bundle.extract(member, destination)

            mode = member.external_attr >> 16
            if mode and not member.is_dir():
                os.chmod(target, mode & 0o7777)


def _collapse_single_root(directory: Path) -> Path:
    """
    Descend through a redundant top-level folder, if the archive has one.

    The release workflow produces archives whose members sit at the root on
    Windows but under a ``release/`` prefix on macOS and Linux. Collapsing
    here means the installer does not need to know which platform produced
    the archive it is applying.

    Parameters
    ----------
    directory : pathlib.Path
        Freshly extracted tree.

    Returns
    -------
    pathlib.Path
        Directory that actually holds the application files.
    """
    entries = [item for item in directory.iterdir() if item.name != "__MACOSX"]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return directory


def _prune_existing_user_data(payload: Path, install_dir: Path) -> List[str]:
    """
    Remove payload files that would overwrite existing user data.

    Parameters
    ----------
    payload : pathlib.Path
        Extracted application tree.
    install_dir : pathlib.Path
        Current installation.

    Returns
    -------
    list of str
        Relative paths that were preserved on disk.
    """
    preserved: List[str] = []

    for folder in USER_DATA_DIRS:
        source = payload / folder
        if not source.is_dir():
            continue

        for item in sorted(source.rglob("*")):
            if item.is_dir():
                continue
            relative = item.relative_to(payload)
            if (install_dir / relative).exists():
                item.unlink()
                preserved.append(str(relative))

        # Leave the directory itself when every file in it was pruned, so an
        # empty folder is still created on a first-time layout change.
        for child in sorted(source.rglob("*"), reverse=True):
            if child.is_dir() and not any(child.iterdir()):
                child.rmdir()

    return preserved


def stage_update(archive: Path, install_dir: Optional[Path] = None) -> InstallPlan:
    """
    Extract and prepare a downloaded archive for installation.

    Parameters
    ----------
    archive : pathlib.Path
        Verified ``.zip`` produced by :class:`update_service.UpdateService`.
    install_dir : pathlib.Path, optional
        Destination; defaults to the install root.

    Returns
    -------
    InstallPlan
        Staged update, ready for :func:`launch_installer`.

    Raises
    ------
    InstallError
        If the destination is unwritable or the archive has no executable.
    """
    install_dir = Path(install_dir or install_root())

    permitted, reason = can_install(install_dir)
    if not permitted:
        raise InstallError(reason)

    staging = install_dir / STAGING_DIRNAME
    shutil.rmtree(staging, ignore_errors=True)
    extract_dir = staging / "extracted"

    _safe_extract(Path(archive), extract_dir)
    payload = _collapse_single_root(extract_dir)

    binary = executable_name()
    if not (payload / binary).is_file():
        raise InstallError(
            f"The downloaded archive does not contain {binary}; it may have "
            f"been built for a different platform.")

    os.chmod(payload / binary, os.stat(payload / binary).st_mode | stat.S_IEXEC
             | stat.S_IXGRP | stat.S_IXOTH)

    preserved = _prune_existing_user_data(payload, install_dir)

    return InstallPlan(
        payload_dir=payload,
        install_dir=install_dir,
        executable_name=binary,
        staging_dir=staging,
        preserved=tuple(preserved),
    )


# =============================================================================
# Helper script generation
# =============================================================================

_POSIX_HELPER = """#!/bin/sh
# Applies a staged Spikeling update once the running instance has exited.
set -u

PID="$1"
PAYLOAD="$2"
INSTALL="$3"
BINARY="$4"
STAGING="$5"

waited=0
while kill -0 "$PID" 2>/dev/null; do
    sleep 0.2
    waited=$((waited + 1))
    if [ "$waited" -gt {timeout_ticks} ]; then
        exit 1
    fi
done

# Keep the old binary: if the copy below fails halfway, the application must
# still be launchable.
if [ -f "$INSTALL/$BINARY" ]; then
    mv -f "$INSTALL/$BINARY" "$INSTALL/$BINARY{backup}"
fi

cp -R "$PAYLOAD/." "$INSTALL/"

if [ ! -f "$INSTALL/$BINARY" ]; then
    mv -f "$INSTALL/$BINARY{backup}" "$INSTALL/$BINARY"
    exit 1
fi

chmod +x "$INSTALL/$BINARY"

# A download inherits the quarantine attribute, which makes Gatekeeper refuse
# an unsigned binary outright rather than offering the usual override.
if command -v xattr >/dev/null 2>&1; then
    xattr -dr com.apple.quarantine "$INSTALL" 2>/dev/null || true
fi

rm -f "$INSTALL/$BINARY{backup}"
cd "$INSTALL" && ./"$BINARY" &

sleep 2
rm -rf "$STAGING"
"""

_WINDOWS_HELPER = """@echo off
rem Applies a staged Spikeling update once the running instance has exited.
setlocal

set "PID=%~1"
set "PAYLOAD=%~2"
set "INSTALL=%~3"
set "BINARY=%~4"
set "STAGING=%~5"
set /a WAITED=0

:waitloop
tasklist /FI "PID eq %PID%" 2>nul | find "%PID%" >nul
if errorlevel 1 goto swap
timeout /t 1 /nobreak >nul
set /a WAITED+=1
if %WAITED% GTR {timeout_seconds} exit /b 1
goto waitloop

:swap
rem Windows permits renaming a locked executable but not overwriting it, so
rem the old binary is moved aside rather than replaced in place.
if exist "%INSTALL%\\%BINARY%" move /y "%INSTALL%\\%BINARY%" "%INSTALL%\\%BINARY%{backup}" >nul

xcopy "%PAYLOAD%\\*" "%INSTALL%\\" /E /I /Y >nul

if not exist "%INSTALL%\\%BINARY%" (
    move /y "%INSTALL%\\%BINARY%{backup}" "%INSTALL%\\%BINARY%" >nul
    exit /b 1
)

del /q "%INSTALL%\\%BINARY%{backup}" 2>nul

cd /d "%INSTALL%"
start "" "%INSTALL%\\%BINARY%"

timeout /t 2 /nobreak >nul
rmdir /s /q "%STAGING%" 2>nul
"""


def _write_helper(plan: InstallPlan) -> Path:
    """Write the platform helper script and return its path."""
    windows = host_platform_key() == "Windows"
    name = "apply_update.cmd" if windows else "apply_update.sh"
    path = plan.staging_dir / name

    template = _WINDOWS_HELPER if windows else _POSIX_HELPER
    body = template.format(
        backup=BACKUP_SUFFIX,
        timeout_seconds=EXIT_TIMEOUT_SECONDS,
        timeout_ticks=EXIT_TIMEOUT_SECONDS * 5,
    )

    path.write_text(body, encoding="utf-8", newline="\r\n" if windows else "\n")
    if not windows:
        path.chmod(0o755)
    return path


def launch_installer(plan: InstallPlan) -> None:
    """
    Start the detached helper that applies ``plan``.

    The caller must quit immediately afterwards: the helper blocks until this
    process exits, then performs the swap and relaunches the application.

    Parameters
    ----------
    plan : InstallPlan
        Result of :func:`stage_update`.

    Raises
    ------
    InstallError
        If the helper cannot be started.
    """
    helper = _write_helper(plan)
    arguments = [
        str(os.getpid()),
        str(plan.payload_dir),
        str(plan.install_dir),
        plan.executable_name,
        str(plan.staging_dir),
    ]

    try:
        if host_platform_key() == "Windows":
            # DETACHED_PROCESS keeps the helper alive past our exit, and
            # CREATE_NO_WINDOW suppresses the console flash.
            subprocess.Popen(
                ["cmd.exe", "/c", str(helper), *arguments],
                close_fds=True,
                creationflags=0x00000008 | 0x08000000,
            )
        else:
            # start_new_session detaches from the process group, so the
            # helper is not killed along with the application.
            subprocess.Popen(
                ["/bin/sh", str(helper), *arguments],
                close_fds=True,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except OSError as error:
        raise InstallError(f"Could not start the update helper: {error}") from error


def cleanup_staging(install_dir: Optional[Path] = None) -> None:
    """
    Remove a leftover staging directory.

    Called at start-up so an interrupted update does not accumulate a
    half-extracted copy of the application next to the executable.
    """
    staging = Path(install_dir or install_root()) / STAGING_DIRNAME
    shutil.rmtree(staging, ignore_errors=True)
