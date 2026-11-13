"""
solarian-gripper1

A plugin for the Solarian robotics framework. Ships two parallel-gripper
modules that share the same finger kinematics and aperture (mm) command
space, differing only in the driving actuator:

* Feetech STS — ``Gripper1FeetechModule`` / ``assets/gripper1.xml``
* Robstride L7 — ``Gripper1RobstrideModule`` / ``assets/gripper1_robstride.xml``
"""

from pathlib import Path

from solarian_gripper_1.aperture import APERTURE_CLOSED_MM, APERTURE_OPEN_MM

__version__ = "0.1.0"

#: Directory holding this plugin's simulation assets (MJCF + meshes). Shipped
#: inside the package (see ``[tool.setuptools.package-data]`` in
#: ``pyproject.toml``) so a robot scene can attach the gripper directly from the
#: installed package instead of copying the model into the project.
ASSETS_DIR = Path(__file__).resolve().parent / "assets"

#: Absolute path to the Feetech-actuated gripper's attachable MJCF.
MJCF_FEETECH_PATH = str(ASSETS_DIR / "gripper1.xml")

#: Absolute path to the Robstride-actuated gripper's attachable MJCF.
MJCF_ROBSTRIDE_PATH = str(ASSETS_DIR / "gripper1_robstride.xml")

#: Historical alias for the Feetech model. Prefer ``MJCF_FEETECH_PATH``.
MJCF_PATH = MJCF_FEETECH_PATH

__all__ = [
    "ASSETS_DIR",
    "MJCF_PATH",
    "MJCF_FEETECH_PATH",
    "MJCF_ROBSTRIDE_PATH",
    "APERTURE_CLOSED_MM",
    "APERTURE_OPEN_MM",
    "__version__",
]
