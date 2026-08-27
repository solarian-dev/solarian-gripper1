"""
solarian-umi-slim

A plugin for the Solarian robotics framework. Ships two parallel-gripper
modules that share the same finger kinematics and aperture (cm) command
space, differing only in the driving actuator:

* Feetech STS — ``UmiSlimFeetechModule`` / ``assets/umi_slim.xml``
* Robstride L7 — ``UmiSlimRobstrideModule`` / ``assets/umi_slim_robstride.xml``
"""

from pathlib import Path

from solarian_umi_slim.aperture import APERTURE_CLOSED_CM, APERTURE_OPEN_CM

__version__ = "0.1.0"

#: Directory holding this plugin's simulation assets (MJCF + meshes). Shipped
#: inside the package (see ``[tool.setuptools.package-data]`` in
#: ``pyproject.toml``) so a robot scene can attach the gripper directly from the
#: installed package instead of copying the model into the project.
ASSETS_DIR = Path(__file__).resolve().parent / "assets"

#: Absolute path to the Feetech-actuated gripper's attachable MJCF.
MJCF_FEETECH_PATH = str(ASSETS_DIR / "umi_slim.xml")

#: Absolute path to the Robstride-actuated gripper's attachable MJCF.
MJCF_ROBSTRIDE_PATH = str(ASSETS_DIR / "umi_slim_robstride.xml")

#: Historical alias for the Feetech model. Prefer ``MJCF_FEETECH_PATH``.
MJCF_PATH = MJCF_FEETECH_PATH

__all__ = [
    "ASSETS_DIR",
    "MJCF_PATH",
    "MJCF_FEETECH_PATH",
    "MJCF_ROBSTRIDE_PATH",
    "APERTURE_CLOSED_CM",
    "APERTURE_OPEN_CM",
    "__version__",
]
