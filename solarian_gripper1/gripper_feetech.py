"""
solarian-gripper1 Feetech module

A parallel gripper driven by a single Feetech servo. It is commanded by the
desired **finger aperture in millimetres**; the core
:class:`~solarian.core.gripper_module.GripperModule` translates that aperture
into the servo's normalized command space, which each backend then maps to the
physical target:

* **Real hardware** — normalized command -> servo counts via the Feetech
  calibration (recorded closed/open positions).
* **Simulation** — the same normalized command drives both jaw joints via
  ``sim_joint`` and ``sim_followers`` in ``conf_gripper_feetech.yaml``. Each
  joint uses the limits its URDF exported. A CAD relation is not required,
  because URDF exports do not carry one.

Because the module always emits the *same* normalized value to
``write_actuators``, real and sim stay consistent as long as their endpoints
(yaml ``real_range_*`` vs. ``sim_range_*``) describe the same physical
apertures configured here as ``aperture_open_mm`` / ``aperture_closed_mm``.

Trajectory upsampling uses the core GripperModule scalar path
(``interpolator_type: scalar`` in yaml): sparse ``SCHEDULE_J`` / ``MOVE_J`` / ``SERVO_J``
apertures are in **millimetres**, interpolated at the module rate, then
converted to normalized servo ``[-100, 100]`` on write.
"""

from logging import getLogger

from pydantic import model_validator

from solarian.core.gripper_module import GripperConfig, GripperModule
from solarian.core.data import PosData
from solarian.core.ik import FrameOffset
from solarian_feetech.actuator import FeetechServo
from solarian_gripper1.aperture import (
    APERTURE_CLOSED_MM,
    APERTURE_OPEN_MM,
    resolve_aperture_limits,
)

logger = getLogger("module")


class Gripper1FeetechConfig(GripperConfig):
    """Config for the Feetech-actuated solarian-gripper1.

    ``aperture_closed_mm`` / ``aperture_open_mm`` are the physical finger
    aperture (fingertip separation) at the two ends of travel. They must
    match the servo calibration and the ``sim_range_*`` joint range. Defaults are
    ruler measurements (fully closed 0 mm, fully open 85 mm). The old CAD
    pair 29.4 / 138.4 is replaced on load.
    """

    aperture_closed_mm: float = APERTURE_CLOSED_MM
    aperture_open_mm: float = APERTURE_OPEN_MM

    @model_validator(mode="after")
    def _reject_legacy_cad_limits(self) -> "Gripper1FeetechConfig":
        self.aperture_closed_mm, self.aperture_open_mm = resolve_aperture_limits(
            self.aperture_closed_mm, self.aperture_open_mm
        )
        return self


class Gripper1FeetechModule(GripperModule):
    config_class = Gripper1FeetechConfig

    # CAD ``tcp`` in the ``flange`` frame (gripper1.xml). test_tcp_site
    # requires these to match the sites to 1e-6, so the quat stays unrounded.
    tcp_from_flange = FrameOffset(
        pos=(0.000039965, 0.000160000, 0.197300027),
        quat=(1.0, -1.8385e-06, -2.3464e-06, -5.5098e-06),
    )

    # Single logical actuator, matching the single physical Feetech servo.
    # Declared so the core scalar interpolator knows which field to drive.
    scalar_actuator = "gripper"
    gripper = FeetechServo(model="sts3215")

    def initialize(self):
        super().initialize()
        lo, hi = self.scalar_limits()
        source = "measured table" if self.cfg.aperture_table else "linear endpoints"
        logger.info(
            "Gripper1 Feetech '%s': aperture %.1f–%.1f mm ↔ servo -100–100 (%s)",
            self.name,
            lo,
            hi,
            source,
        )

        # Gentle position-control gains for the gripper servo. These are no-ops
        # in simulation (the MuJoCo world ignores hardware config writes).
        self.disable_torque()
        self.configure_components({
            "Return_Delay_Time": 0,
            "Maximum_Acceleration": 254,
            "Acceleration": 254,
            "Operating_Mode": 0,
            "P_Coefficient": 32,
            "I_Coefficient": 2,
            "D_Coefficient": 2,
        })
        # Hold present before torque-on so a stale Goal_Position cannot slam
        # the jaws into a hard stop on startup.
        self._hold_present_pose()
        self.enable_torque()

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

