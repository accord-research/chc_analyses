"""Shared Jataware styling for AGU-autoscience versions (v0, v1, …).

The single source of truth for the Jataware logo is the design-system directory
`Desktop/JATAWARE/style-resources/` — NOT a per-analysis copy. Render scripts call
`logo_path()` so the logo is never duplicated into an analysis subdir again.
"""
from __future__ import annotations
import os
from pathlib import Path

# The design-system logo lives outside the ACCORD repo, in the sibling JATAWARE workspace.
_ENV = "JATAWARE_STYLE_RESOURCES"
_LOGO_GLOB = "*jataware_logo*.png"


def style_resources_dir() -> Path:
    """Locate JATAWARE/style-resources: env override → walk up for a sibling JATAWARE →
    ~/Desktop/JATAWARE. Raises with a clear message if none exists."""
    if os.environ.get(_ENV):
        d = Path(os.environ[_ENV]).expanduser()
        if d.is_dir():
            return d
    # walk upward looking for a sibling `JATAWARE/style-resources`
    for base in Path(__file__).resolve().parents:
        cand = base / "JATAWARE" / "style-resources"
        if cand.is_dir():
            return cand
    home = Path.home() / "Desktop" / "JATAWARE" / "style-resources"
    if home.is_dir():
        return home
    raise FileNotFoundError(
        "Could not locate JATAWARE/style-resources. Set the "
        f"{_ENV} environment variable to its path."
    )


def logo_path() -> Path:
    """Absolute path to the Jataware logo in the shared style-resources dir."""
    d = style_resources_dir()
    hits = sorted(d.glob(_LOGO_GLOB))
    # prefer the full blue mark if several are present
    blue = [h for h in hits if "blue" in h.name.lower()]
    chosen = (blue or hits)
    if not chosen:
        raise FileNotFoundError(f"No logo matching {_LOGO_GLOB!r} in {d}")
    return chosen[0]


if __name__ == "__main__":
    print(logo_path())
