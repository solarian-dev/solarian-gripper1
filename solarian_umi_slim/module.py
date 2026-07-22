"""
UmiSlim Module

A Solarian module that groups actuators/sensors and runs a control loop.
"""

from solarian.core.module import Module
from solarian.core.action import ActionType, ModuleAction, action_handler


class UmiSlimModule(Module):
    """
    Module for umi-slim.

    Declare actuators and sensors as class attributes, e.g.:

        from solarian_umi_slim.actuator import UmiSlimServo

        class UmiSlimModule(Module):
            shoulder = UmiSlimServo()
    """

    # Declare actuators and sensors here as class attributes.

    def initialize(self):
        # One-time module setup, e.g.:
        self.next_position = None

    def control_step(self):
        # Per-tick control logic, e.g.:
        if getattr(self, "next_position", None) is not None:
            self.write_actuators(self.next_position)
            self.next_position = None

    @action_handler(ActionType.SCHEDULE_WAYPOINT)
    def _handle_schedule_waypoint(self, action: ModuleAction, t_now: float) -> bool:
        self.next_position = action.values()
        return True
