"""
Single source of truth for the application version.

The string is committed rather than derived at runtime: a frozen binary has
no ``.git`` directory, and reading the tag from the environment would leave
locally built binaries claiming to be whatever was last released. The release
workflow verifies that this value matches the pushed tag and fails the build
on a mismatch, so the two cannot drift.

Format follows the release tags: ``v<major>.<minor>.<patch>`` with an optional
pre-release suffix, for example ``v2.1.0`` or ``v2.1.0-rc.1``.
"""

from __future__ import annotations

#: Version of this build. Bump together with the git tag.
__version__ = "v3.1.4"

#: Repository queried for updates. Must match the public GitHub path.
GITHUB_OWNER = "OpenSourceNeuro"
GITHUB_REPO = "Spikeling"

#: Human-facing links used by the GitHub page.
REPOSITORY_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"
RELEASES_URL = f"{REPOSITORY_URL}/releases"
ISSUES_URL = f"{REPOSITORY_URL}/issues"
