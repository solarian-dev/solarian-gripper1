"""
solarian-umi-slim

A plugin for the Solarian robotics framework.
"""

from pathlib import Path

from solarian_umi_slim.aperture import APERTURE_CLOSED_CM, APERTURE_OPEN_CM

__version__ = "0.1.0"

#: Directory holding this plugin's simulation assets (MJCF + meshes). Shipped
#: inside the package (see ``[tool.setuptools.package-data]`` in
#: ``pyproject.toml``) so a robot scene can attach the gripper directly from the
#: installed package instead of copying the model into the project.
ASSETS_DIR = Path(__file__).resolve().parent / "assets"

#: Absolute path to the gripper's attachable MJCF. Pass this to a
#: ``ModuleAttachment(mjcf=...)`` so the scene loads the model (and its meshes,
#: resolved relative to this file) straight from the installed plugin.
MJCF_PATH = str(ASSETS_DIR / "umi_slim.xml")

__all__ = [
    "ASSETS_DIR",
    "MJCF_PATH",
    "APERTURE_CLOSED_CM",
    "APERTURE_OPEN_CM",
    "__version__",
]
