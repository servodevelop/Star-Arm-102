"""Two independent leaders exposed as one LeRobot teleoperator."""

from collections import deque
import logging

from lerobot.teleoperators.teleoperator import Teleoperator
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from lerobot_stararm102_dual import hover, sdk, startup
from lerobot_stararm102_dual.common import JOINTS, SIDES, features, open_buses, stop_buses

from .config import Stararm102DualLeaderConfig

logger = logging.getLogger(__name__)


class StartupGesture:
    """Poll one leader's fresh startup gesture without blocking its peer."""

    def __init__(self, bus, *, side, button_enabled, button_id):
        self.bus = bus
        self.side = side
        self.button_enabled = button_enabled
        self.button_id = button_id
        self.done = False
        self.initial_button = None
        self.gripper = sdk.GripperGesture()
        if button_enabled and bus.button_protocol == "command":
            bus.button_uart.discard_commands()
            self.initial_sequence = bus.button_uart.sequence
            logger.info("%s: press the new button board to unlock; press again if the first press locks", side)
        elif button_enabled:
            logger.info("%s: press the button board after this prompt", side)
        else:
            bus.stop_on_control_mode(6, 0x10, 0)
            logger.info("%s: move the gripper about 5 degrees and back to unlock", side)

    def poll(self):
        if self.done:
            return True
        bus = self.bus
        if self.button_enabled and bus.button_protocol == "command":
            bus.button_uart.poll()
            detected = (bus.button_uart.sequence != self.initial_sequence
                        and bus.button_uart.locked is False)
        else:
            sensor_id = self.button_id if self.button_enabled else 6
            sample = bus.send_sync_servo_monitor([sensor_id], realtime=True).get(sensor_id)
            angle = sample.angle_monitor if sample is not None else None
            if self.button_enabled:
                detected = False
                if angle in (0, 90, 180):
                    if self.initial_button is None:
                        self.initial_button = angle
                    elif angle != self.initial_button:
                        detected = True
            else:
                detected = self.gripper.update(angle)
        if detected:
            bus.stop_on_control_mode(0xff, 0x10, 0)
            self.done = True
            logger.info("%s: startup gesture detected; following enabled", self.side)
        return self.done


class Stararm102DualLeader(Teleoperator):
    config_class = Stararm102DualLeaderConfig
    name = "stararm102_dual_leader"

    def __init__(self, config: Stararm102DualLeaderConfig):
        super().__init__(config)
        self.config = config
        self._stack = None
        self._reference_started = False
        self.buses = {}
        self.buttons = {}
        self.filters = {side: deque(maxlen=getattr(config, f"{side}_filter_size")) for side in SIDES}
        self.hovers = {
            side: hover.HoverState(index, getattr(config, f"{side}_hover_release_threshold"))
            for index, side in enumerate(SIDES, 1)
        }
        self.gestures = {}

    @property
    def action_features(self):
        return features()

    @property
    def feedback_features(self):
        return {}

    @property
    def is_connected(self):
        return self._stack is not None

    @property
    def is_calibrated(self):
        return True

    def calibrate(self):
        pass

    def configure(self):
        for bus in self.buses.values():
            bus.stop_on_control_mode(0xff, 0x10, 0)
            bus.reset_multi_turn_angle(0xff)
            sdk.send_angles(bus, sdk.REFERENCE_ANGLES, sdk.STARTUP_INTERVAL_MS)

    def connect(self, calibrate=True):
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")
        enabled = {side: getattr(self.config, f"{side}_button_enabled") for side in SIDES}
        stack, buses = open_buses((self.config.left_port, self.config.right_port), enabled)
        self._stack, self.buses = stack, buses
        try:
            for side, bus in buses.items():
                if enabled[side]:
                    button_id = getattr(self.config, f"{side}_button_id")
                    bus.button_protocol = "legacy" if any(bus.ping(button_id) for _ in range(3)) else "command"
            startup.register(self, "leader")
        except BaseException:
            self.disconnect()
            raise

    def _prepare_gestures(self):
        for side, bus in self.buses.items():
            self.gestures[side] = StartupGesture(
                bus, side=side,
                button_enabled=getattr(self.config, f"{side}_button_enabled"),
                button_id=getattr(self.config, f"{side}_button_id"),
            )

    def get_action(self):
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected")
        startup.ensure_started(self)
        if not self.gestures:
            self._prepare_gestures()
        action = {}
        for side, bus in self.buses.items():
            if not self.gestures[side].poll():
                action.update({f"{side}.{joint}.pos": float(angle)
                               for joint, angle in zip(JOINTS, sdk.REFERENCE_ANGLES, strict=True)})
                continue
            if side not in self.buttons and getattr(self.config, f"{side}_button_enabled"):
                if bus.button_protocol == "command":
                    self.buttons[side] = sdk.CommandButtonState(bus.button_uart)
                else:
                    button_id = getattr(self.config, f"{side}_button_id")
                    self.buttons[side] = sdk.ButtonState(button_id, unlocked_angle=bus.servos[button_id].angle_monitor)
            if not self.filters[side]:
                self.hovers[side].reset(list(sdk.REFERENCE_ANGLES))
            button = self.buttons.get(side)
            angles = sdk.read_angles(bus, button.id if button else None)
            filtered = sdk.filtered_angles(self.filters[side], angles)
            if button:
                was_locked = button.locked
                locked = button.update(bus)
                if self.config.hover:
                    if locked or was_locked or getattr(button, "changed", False):
                        self.hovers[side].reset(filtered)
                    else:
                        self.hovers[side].update(bus, filtered)
            elif self.config.hover:
                self.hovers[side].update(bus, filtered, gripper_unlock=True)
            action.update({f"{side}.{joint}.pos": float(angle) for joint, angle in zip(JOINTS, filtered, strict=True)})
        return action

    def send_feedback(self, feedback):
        if feedback:
            raise NotImplementedError("Dual leader has no feedback channels")

    def disconnect(self):
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected")
        for error in stop_buses(self.buses, leader=True):
            logger.error("Damping stop failed: %s", error)
        self._stack.close()
        self._stack, self.buses = None, {}
        self._reference_started = False
        self.gestures.clear()
        self.buttons.clear()
        for buffer in self.filters.values():
            buffer.clear()
        startup.unregister(self)
