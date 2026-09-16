"""Physical fingertip aperture at the UMI-slim servo ends.

Ruler measurement on the real gripper: fully closed = 0 mm, fully open = 85 mm.

The old CAD pair (29.4 / 138.4) double-counted both fingers' rail travel. A
stale config with those values maps an 85 mm command to servo ~2, while an
0-85 observation map reports that as ~43 mm. Treat the CAD pair as invalid.
"""

from __future__ import annotations

APERTURE_CLOSED_MM = 0.0
APERTURE_OPEN_MM = 85.0

# Known-bad CAD endpoints. Do not use for mm <-> servo conversion.
_LEGACY_CLOSED_MM = 29.4
_LEGACY_OPEN_MM = 138.4


def resolve_aperture_limits(
    closed_mm: float, open_mm: float
) -> tuple[float, float]:
    """Return (closed, open) mm, replacing legacy CAD or inverted values."""
    lo, hi = float(closed_mm), float(open_mm)
    if abs(lo - _LEGACY_CLOSED_MM) < 0.5 or abs(hi - _LEGACY_OPEN_MM) < 0.5:
        return APERTURE_CLOSED_MM, APERTURE_OPEN_MM
    if hi <= lo:
        return APERTURE_CLOSED_MM, APERTURE_OPEN_MM
    return lo, hi
