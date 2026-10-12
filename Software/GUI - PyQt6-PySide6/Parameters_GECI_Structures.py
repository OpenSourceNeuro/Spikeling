"""
Structural metadata for the calcium indicators in ``Parameters_GECI.GECI``.

Genetically encoded calcium indicators are synthetic fusions (circularly
permuted fluorescent protein + calmodulin + M13 peptide), so structural
coverage is partial: parent scaffolds are crystallised, most engineered
variants are not. Entries therefore carry an explicit ``is_representative``
flag, and the preview caption states when the rendered structure is a
family scaffold rather than the variant itself.

The ``suggested_pdb_id`` fields are *unverified seeds*. Call
:func:`resolve_pdb_id` once per indicator to confirm them against the RCSB
search API and commit the resulting cache file.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

RCSB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_DOWNLOAD_URL = "https://files.rcsb.org/download/{pdb_id}.cif"
MODULE_DIRECTORY = Path(__file__).resolve().parent
PDB_ID_CACHE = MODULE_DIRECTORY / "resources" / "geci" / "pdb_ids.json"

@dataclass(frozen=True)
class GeciStructure:
    """
    Structural provenance for one indicator.

    Attributes
    ----------
    scaffold : str
        Molecular architecture, e.g. ``"cpGFP + CaM + M13"``.
    suggested_pdb_id : str
        Unverified starting point; superseded by the resolver cache.
    rcsb_query : str
        Full-text query used to resolve the accession code.
    is_representative : bool
        ``True`` when no structure of this exact variant is deposited and a
        family member is shown instead.
    caption : str
        Line displayed under the rotating render.
    """

    scaffold: str
    suggested_pdb_id: str
    rcsb_query: str
    is_representative: bool
    caption: str


GECI_STRUCTURES: dict[str, GeciStructure] = {
    "Generic": GeciStructure(
        "cpGFP + CaM + M13", "3EK4", "GCaMP calcium sensor",
        True, "Representative GCaMP-family scaffold (Ca²⁺-bound)"),
    "GCaMP2": GeciStructure(
        "cpEGFP + CaM + M13", "3EK4", "GCaMP2 calcium sensor crystal structure",
        False, "GCaMP2, Ca²⁺-bound"),
    "GCaMP6s": GeciStructure(
        "cpEGFP + CaM + M13", "3EK4", "GCaMP6 calcium indicator",
        True, "GCaMP-family scaffold — GCaMP6s differs by point mutations"),
    "GCaMP6m": GeciStructure(
        "cpEGFP + CaM + M13", "3EK4", "GCaMP6 calcium indicator",
        True, "GCaMP-family scaffold — GCaMP6m differs by point mutations"),
    "GCaMP6f": GeciStructure(
        "cpEGFP + CaM + M13", "3EK4", "GCaMP6 calcium indicator",
        True, "GCaMP-family scaffold — GCaMP6f differs by point mutations"),
    "R-GECO1": GeciStructure(
        "cpmApple + CaM + M13", "", "R-GECO1 red calcium indicator",
        False, "R-GECO1, cpmApple-based red indicator"),
    "jRGECO1a": GeciStructure(
        "cpmApple + CaM + M13", "", "R-GECO red calcium indicator",
        True, "R-GECO scaffold — jRGECO1a not crystallised"),
    "jRCaMP1a": GeciStructure(
        "cpmRuby + CaM + M13", "", "RCaMP red calcium indicator",
        True, "RCaMP scaffold — jRCaMP1a not crystallised"),
    "f-RGECO1": GeciStructure(
        "cpmApple + CaM + M13", "", "R-GECO red calcium indicator",
        True, "R-GECO scaffold — fast variant not crystallised"),
    "f-RGECO2": GeciStructure(
        "cpmApple + CaM + M13", "", "R-GECO red calcium indicator",
        True, "R-GECO scaffold — fast variant not crystallised"),
    "f-RCaMP1": GeciStructure(
        "cpmRuby + CaM + M13", "", "RCaMP red calcium indicator",
        True, "RCaMP scaffold — fast variant not crystallised"),
    "f-RCaMP2": GeciStructure(
        "cpmRuby + CaM + M13", "", "RCaMP red calcium indicator",
        True, "RCaMP scaffold — fast variant not crystallised"),
}


def resolve_pdb_id(geci_name: str, use_cache: bool = True) -> Optional[str]:
    """
    Resolve an accession code for ``geci_name`` against the RCSB search API.

    Parameters
    ----------
    geci_name : str
        Key into :data:`GECI_STRUCTURES`.
    use_cache : bool, optional
        Read and write ``resources/geci/pdb_ids.json`` so the network is
        queried once per indicator rather than once per build.

    Returns
    -------
    str or None
        Four-character PDB identifier, or ``None`` when nothing matches.

    Notes
    -----
    Run this at packaging time, never from the GUI event loop: it performs a
    blocking HTTPS request.
    """
    cache: dict[str, str] = {}
    if use_cache and PDB_ID_CACHE.exists():
        cache = json.loads(PDB_ID_CACHE.read_text(encoding="utf-8"))
        if geci_name in cache:
            return cache[geci_name] or None

    entry = GECI_STRUCTURES.get(geci_name)
    if entry is None:
        return None

    payload = {
        "query": {"type": "terminal", "service": "full_text",
                  "parameters": {"value": entry.rcsb_query}},
        "return_type": "entry",
        "request_options": {"paginate": {"start": 0, "rows": 5}},
    }
    url = f"{RCSB_SEARCH_URL}?json={urllib.parse.quote(json.dumps(payload))}"

    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            hits = json.loads(response.read()).get("result_set", [])
    except Exception as error:
        print(f"RCSB lookup failed for {geci_name}: {error}")
        return entry.suggested_pdb_id or None

    pdb_id = hits[0]["identifier"] if hits else (entry.suggested_pdb_id or "")

    if use_cache:
        PDB_ID_CACHE.parent.mkdir(parents=True, exist_ok=True)
        cache[geci_name] = pdb_id
        PDB_ID_CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")

    return pdb_id or None


def structure_download_url(pdb_id: str) -> str:
    """Return the mmCIF download URL for ``pdb_id``."""
    return RCSB_DOWNLOAD_URL.format(pdb_id=pdb_id.upper())
