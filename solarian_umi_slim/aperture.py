"""Physical fingertip aperture at the UMI-slim servo ends.

Ruler measurement on the real gripper: fully closed = 0 cm, fully open = 8.5 cm.

The old CAD pair (2.94 / 13.84) double-counted both fingers' rail travel. A
stale config with those values maps an 8.5 cm command to servo ~2, while a
0–8.5 observation map reports that as ~4.3 cm. Treat the CAD pair as invalid.
"""

from __future__ import annotations

APERTURE_CLOSED_CM = 0.0
APERTURE_OPEN_CM = 8.5

# Known-bad CAD endpoints. Do not use for cm ↔ servo conversion.
_LEGACY_CLOSED_CM = 2.94
_LEGACY_OPEN_CM = 13.84


def resolve_aperture_limits(
    closed_cm: float | None = None,
    open_cm: float | None = None,
) -> tuple[float, float]:
    """Return (closed, open) cm, replacing missing or legacy CAD values."""
    lo = APERTURE_CLOSED_CM if closed_cm is None else float(closed_cm)
    hi = APERTURE_OPEN_CM if open_cm is None else float(open_cm)
    if abs(lo - _LEGACY_CLOSED_CM) < 0.05 or abs(hi - _LEGACY_OPEN_CM) < 0.05:
        return APERTURE_CLOSED_CM, APERTURE_OPEN_CM
    if hi <= lo:
        return APERTURE_CLOSED_CM, APERTURE_OPEN_CM
    return lo, hi


def aperture_to_norm(
    aperture_cm: float,
    closed_cm: float | None = None,
    open_cm: float | None = None,
) -> float:
    """Map finger aperture (cm) to normalized servo command [-100, 100]."""
    lo, hi = resolve_aperture_limits(closed_cm, open_cm)
    norm = (float(aperture_cm) - lo) / (hi - lo) * 200.0 - 100.0
    return max(-100.0, min(100.0, norm))


def norm_to_aperture(
    norm: float,
    closed_cm: float | None = None,
    open_cm: float | None = None,
) -> float:
    """Inverse of :func:`aperture_to_norm` (normalized [-100, 100] → cm)."""
    lo, hi = resolve_aperture_limits(closed_cm, open_cm)
    return lo + ((float(norm) + 100.0) / 200.0) * (hi - lo)
