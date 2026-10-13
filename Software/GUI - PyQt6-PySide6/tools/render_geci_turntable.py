"""
Offline turntable renderer for the GECI hover previews.

Produces ``resources/geci/<GECI>/frame_000.png ...`` with a transparent
background. Run once at packaging time; PyMOL is a build dependency only and
is never imported by the GUI.

Usage
-----
    pymol -cq tools/render_geci_turntable.py -- --frames 36 --size 440

Notes
-----
PyMOL executes scripts through ``execfile`` without extending ``sys.path``
and without a reliable ``__file__``, so the repository root is located by
searching for a marker module before the project imports are performed.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from pymol import cmd

REPOSITORY_MARKER = "Parameters_GECI.py"
CHROMOPHORE_RESNAMES = "CRO+CR2+CRQ+CSY+NRQ+GYS+CFY+CH6+IEY"
CALCIUM_RESNAMES = "CA+CAL"


def locate_repository_root(marker: str = REPOSITORY_MARKER) -> Path:
    """
    Find the Spikeling source root so project modules become importable.

    Parameters
    ----------
    marker : str
        File whose presence identifies the repository root.

    Returns
    -------
    pathlib.Path
        Directory containing ``marker``.

    Raises
    ------
    RuntimeError
        When no candidate directory contains the marker; set
        ``SPIKELING_ROOT`` to resolve this explicitly.

    Notes
    -----
    Candidates are probed in decreasing order of trustworthiness: the
    ``SPIKELING_ROOT`` override, the script location when ``__file__`` happens
    to be meaningful, then the working directory and each of its ancestors.
    """
    candidates: list[Path] = []

    override = os.environ.get("SPIKELING_ROOT")
    if override:
        candidates.append(Path(override).expanduser().resolve())

    module_file = globals().get("__file__")
    if module_file and Path(module_file).name == "render_geci_turntable.py":
        script_path = Path(module_file).resolve()
        candidates += [script_path.parent, script_path.parent.parent]

    working_directory = Path.cwd().resolve()
    candidates += [working_directory, *working_directory.parents]

    for candidate in candidates:
        if (candidate / marker).is_file():
            return candidate

    raise RuntimeError(
        f"Could not locate {marker}. Run from the repository root, or set "
        f"SPIKELING_ROOT=/path/to/Spikeling."
    )


REPOSITORY_ROOT = locate_repository_root()
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from Parameters_GECI_Structures import GECI_STRUCTURES, resolve_pdb_id  # noqa: E402


def script_arguments() -> list[str]:
    """
    Extract the user arguments from PyMOL's rewritten ``sys.argv``.

    PyMOL forwards everything after ``--`` but the exact shape of ``argv[0]``
    varies between builds, so interpreter and script tokens are filtered out
    rather than assumed to occupy a fixed position.
    """
    argv = list(sys.argv)
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = argv[1:]
    return [token for token in argv
            if not token.endswith(".py") and token not in ("pymol", "-c", "-q", "-cq")]


def render_turntable(pdb_id: str, out_dir: Path, n_frames: int, size: int,
                     fetch_path: Path) -> bool:
    """
    Render one full y-axis rotation of ``pdb_id`` as transparent PNG frames.

    Parameters
    ----------
    pdb_id : str
        RCSB accession code, fetched into a clean PyMOL session.
    out_dir : pathlib.Path
        Destination directory, created if absent.
    n_frames : int
        Frames per revolution; 36 gives 10 degree steps and a 1.2 s loop at 30 fps.
    size : int
        Square render size in pixels; render at twice the display size so the
        preview stays sharp on HiDPI screens.
    fetch_path : pathlib.Path
        Local mmCIF cache, so repeated runs do not re-download structures.

    Returns
    -------
    bool
        ``True`` on success, ``False`` when the structure could not be fetched
        or contained no polymer.

    Notes
    -----
    Cartoon backbone, Ca2+ ions as spheres and the chromophore as sticks: the
    three features needed to read the sensing mechanism at tooltip size.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    fetch_path.mkdir(parents=True, exist_ok=True)

    cmd.reinitialize()
    cmd.set("fetch_path", str(fetch_path))

    try:
        cmd.fetch(pdb_id, "sensor", type="cif", async_=0)
    except Exception as error:
        print(f"  fetch failed for {pdb_id}: {error}")
        return False

    if cmd.count_atoms("polymer") == 0:
        print(f"  {pdb_id} contains no polymer, skipped")
        return False

    cmd.remove("solvent")
    cmd.hide("everything")

    cmd.show("cartoon", "polymer")
    cmd.spectrum("count", "skyblue white salmon", "polymer and name CA")
    cmd.show("spheres", f"resn {CALCIUM_RESNAMES}")
    cmd.color("gold", f"resn {CALCIUM_RESNAMES}")
    cmd.show("sticks", f"resn {CHROMOPHORE_RESNAMES}")
    cmd.color("limon", f"resn {CHROMOPHORE_RESNAMES}")

    cmd.set("ray_opaque_background", 0)
    cmd.set("antialias", 2)
    cmd.set("specular", 0.2)
    cmd.orient("polymer")
    cmd.zoom("polymer", buffer=2.0)

    step_deg = 360.0 / n_frames
    for index in range(n_frames):
        cmd.png(str(out_dir / f"frame_{index:03d}.png"),
                width=size, height=size, dpi=150, ray=1)
        cmd.turn("y", step_deg)

    return True


def main() -> None:
    """Resolve every indicator's structure and render its turntable."""
    parser = argparse.ArgumentParser(description="Render GECI turntable sprites.")
    parser.add_argument("--frames", type=int, default=36)
    parser.add_argument("--size", type=int, default=440)
    parser.add_argument("--out", type=Path, default=REPOSITORY_ROOT / "resources" / "geci")
    parser.add_argument("--cache", type=Path, default=REPOSITORY_ROOT / ".cache" / "pdb")
    parser.add_argument("--only", nargs="*", default=None,
                        help="Restrict rendering to these indicator names.")
    arguments, _ = parser.parse_known_args(script_arguments())

    names = arguments.only or list(GECI_STRUCTURES)
    rendered, skipped = 0, 0

    for geci_name in names:
        pdb_id = resolve_pdb_id(geci_name)
        if not pdb_id:
            print(f"[skip]   {geci_name}: no structure resolved")
            skipped += 1
            continue

        print(f"[render] {geci_name} <- {pdb_id}")
        if render_turntable(pdb_id, arguments.out / geci_name,
                            arguments.frames, arguments.size, arguments.cache):
            rendered += 1
        else:
            skipped += 1

    print(f"\nDone: {rendered} rendered, {skipped} skipped -> {arguments.out}")


main()
