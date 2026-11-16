"""
solarian-gripper1 Robstride module

A parallel gripper driven by a single Robstride L7. Same finger kinematics
and aperture-in-millimetres command space as the Feetech variant; only the
actuator backend differs.

* **Real hardware** — normalized command -> motor counts via the Robstride
  calibration (recorded closed/open positions).
* **Simulation** — the same normalized command drives both jaw joints via
  ``sim_joint`` and ``sim_followers`` in ``conf_gripper_robstride.yaml``. Each
  joint uses the limits its URDF exported.

Trajectory upsampling uses the core GripperModule scalar path
(``interpolator_type: scalar`` in yaml): sparse ``SCHEDULE_J`` / ``MOVE_J`` / ``SERVO_J``
apertures are in **millimetres**, interpolated at the module rate, then
converted to normalized servo ``[-100, 100]`` on write.
"""

from logging import getLogger
import time

from pydantic import model_validator

from solarian.core.gripper_module import GripperConfig, GripperModule
from solarian.core.data import PosData
from solarian.core.ik import FrameOffset
from solarian_robstride.actuator import RobstrideServo
from solarian_gripper1.aperture import (
    APERTURE_CLOSED_MM,
    APERTURE_OPEN_MM,
    resolve_aperture_limits,
)

logger = getLogger("module")


class Gripper1RobstrideConfig(GripperConfig):
    """Config for the Robstride-actuated solarian-gripper1.

    ``aperture_closed_mm`` / ``aperture_open_mm`` are the physical finger
    aperture (fingertip separation) at the two ends of travel. They must
    match the servo calibration and the ``sim_range_*`` joint range. Defaults are
    ruler measurements (fully closed 0 mm, fully open 85 mm).
    """

    aperture_closed_mm: float = APERTURE_CLOSED_MM
    aperture_open_mm: float = APERTURE_OPEN_MM

    @model_validator(mode="after")
    def _reject_legacy_cad_limits(self) -> "Gripper1RobstrideConfig":
        self.aperture_closed_mm, self.aperture_open_mm = resolve_aperture_limits(
            self.aperture_closed_mm, self.aperture_open_mm
        )
        return self


class Gripper1RobstrideModule(GripperModule):
    config_class = Gripper1RobstrideConfig

    # CAD ``tcp`` in the ``flange`` frame (gripper1_robstride.xml). +Z of flange.
    # test_tcp_site checks these against the sites to 1e-6.
    tcp_from_flange = FrameOffset(
        pos=(0.0, 0.0, 0.21415),
        quat=(1.0, 0.0, 0.0, 0.0),
    )

    # Single logical actuator, matching the single physical Robstride L7.
    # Declared so the core scalar interpolator knows which field to drive.
    scalar_actuator = "gripper"
    gripper = RobstrideServo(model="el05")

    def initialize(self):
        super().initialize()
        lo, hi = self.scalar_limits()
        source = "measured table" if self.cfg.aperture_table else "linear endpoints"
        logger.info(
            "Gripper1 Robstride '%s': aperture %.1f–%.1f mm ↔ servo -100–100 (%s)",
            self.name,
            lo,
            hi,
            source,
        )

        self.disable_torque()
        self.configure_components(
            {
                "run_mode": 5,  # CSP
                "limit_spd": 4.0,
            },
            component_names=["gripper"],
        )
        self.enable_torque()
        time.sleep(0.05)
        self._hold_present_pose()

    # ---- safety hooks (called by the align-ik CLI) -------------------------
    def _hold_present_pose(self) -> None:
        """Latch Goal to the raw encoder so torque-on cannot slam."""
        present = self.read_sensors(PosData, ["gripper"], normalize=False)
        self.module_bus.write(
            {"gripper": PosData(value=present["gripper"]["value"])},
            normalize=False,
        )

    def enter_safe_hold(self) -> None:
        """Hold the gripper where it is until armed (no jump on power-up)."""
        self._hold_present_pose()
        self.enable_torque()

    def on_arm(self) -> None:
        """Re-hold + re-enable torque so arming never jumps the gripper."""
        self._hold_present_pose()
        self.enable_torque()

    def on_disarm(self) -> None:
        pass
