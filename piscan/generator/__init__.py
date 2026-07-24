"""PIScanner payload generation framework.

A layered, composable pipeline that expands a few hundred curated seed payloads
into tens of thousands of *unique* attack payloads while preserving full
provenance for every generated item.

Layers
------
1. Seeds        (seeds.py)      curated base payloads, tagged with goal + subcategory
2. Mutations    (mutations.py)  encoding / unicode / spacing transforms (composable)
3. Personas     (personas.py)   same attack spoken by different personas
4. Wrappers     (wrappers.py)   attack embedded in email / PDF / CSV / JSON / ...
5. Languages    (languages.py)  localized variants via a curated phrasebook
6. Goals        (goals.py)      attack objective -> success marker mapping
Pipeline        (pipeline.py)   budgeted sampler + hash dedup + provenance
Export          (export.py)     JSONL / split-JSON export + stats report

The generated payloads keep a detector-compatible ``category`` (one of the seven
PIScanner detector categories) so existing detection works unchanged, while the
finer 25-way taxonomy is carried in ``subcategory``.
"""

from .pipeline import Generator, GenConfig  # noqa: F401

__all__ = ["Generator", "GenConfig"]
