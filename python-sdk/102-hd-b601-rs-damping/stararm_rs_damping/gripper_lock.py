"""Software contact wall for a Leader gripper; no hardware writes are made here."""
from dataclasses import dataclass, fields, replace
import math


# Leader backlash must not become an opening command after a single frame.
OPEN_RELEASE_DWELL_S = .06


@dataclass(frozen=True)
class GripperLockConfig:
    enabled: bool = False
    closing_sign: int = -1
    hold_mw: int = 1200
    contact_torque_nm: float = .45
    release_torque_nm: float = .20
    contact_dwell_s: float = .12
    release_dwell_s: float = .10
    error_motor_deg: float = 3.
    closed_end_margin_motor_deg: float = 8.
    max_speed_rad_s: float = .25
    motion_filter_s: float = .10
    open_release_leader_deg: float = .4
    open_release_dwell_s: float = OPEN_RELEASE_DWELL_S
    drop_close_motor_deg: float = 5.
    source_age_s: float = .15

    def __post_init__(self):
        if type(self.enabled) is not bool:
            raise ValueError('enabled must be a boolean')
        if type(self.closing_sign) is not int or self.closing_sign not in (-1, 1):
            raise ValueError('closing_sign must be -1 or 1 in Leader coordinates')
        if type(self.hold_mw) is not int or not 100 <= self.hold_mw <= 1500:
            raise ValueError('hold_mw must be an integer within 100..1500 mW')
        for field in fields(self):
            if field.name in ('enabled', 'closing_sign', 'hold_mw'):
                continue
            value = getattr(self, field.name)
            if not _finite(value) or value <= 0:
                raise ValueError(f'{field.name} must be finite and positive')
        if self.release_torque_nm >= self.contact_torque_nm:
            raise ValueError('release torque must be lower than contact torque')
        if not .02 <= self.source_age_s <= .25:
            raise ValueError('source_age_s must be within .02.. .25 seconds')


def _finite(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value))


class GripperLock:
    """Detect contact and request bounded HOLD, releasing on opening movement.

    HOLD itself is bidirectional. The caller must release it when ``hold`` is
    false; opening is detected from a small real Leader displacement. This is
    a software wall, not a rigid mechanical one-way brake.
    """

    def __init__(self, config=None):
        self.config = config if config is not None else GripperLockConfig()
        if not isinstance(self.config, GripperLockConfig):
            raise TypeError('config must be GripperLockConfig')
        self.reset()

    def reset(self, reason='reset'):
        self.phase = 'FREE' if self.config.enabled else 'DISABLED'
        self.reason = reason if self.config.enabled else 'disabled'
        self.contact = self.hold = False
        self.wall_leader_deg = self.wall_target_leader_deg = None
        self._contact_motor_deg = None
        self._hold_leader_deg = self._open_peak_leader_deg = None
        self._opening_since = None
        self._candidate_most_closed_leader_deg = self._candidate_open_peak_leader_deg = None
        self._candidate_since = self._release_since = None
        self._last_received_at = self._last_now = None
        self._previous_motor_deg = None
        self.estimated_velocity_rad_s = 0.

    @property
    def power_mw(self):
        return self.config.hold_mw if self.hold else 0

    def _invalid(self, reason):
        self.reset('invalid: ' + reason)
        self.phase = 'INVALID'
        return self

    def invalidate(self, reason):
        """Release state after a gap/suspension without changing configuration."""
        return self._invalid(str(reason))

    def configure(self, config):
        """Apply validated settings; a power-only change preserves contact."""
        if not isinstance(config, GripperLockConfig):
            raise TypeError('config must be GripperLockConfig')
        power_only = replace(self.config, hold_mw=config.hold_mw) == config
        self.config = config
        if not power_only:
            self.reset('configuration changed; waiting for contact')
        return self

    def _free(self, reason):
        # Keep sample ordering across an ordinary contact release.
        received, now = self._last_received_at, self._last_now
        self.reset(reason)
        self._last_received_at, self._last_now = received, now

    def _sample(self, state, scale, limits, now):
        try:
            q, velocity, torque, received = state.pos, state.vel, state.torq, state.received_at
            low, high = limits
        except (AttributeError, TypeError, ValueError):
            self._invalid('missing motor state or limits')
            return None
        if not all(_finite(v) for v in (q, velocity, torque, received, scale, low, high, now)):
            self._invalid('non-finite state, mapping or timestamp')
            return None
        cfg = self.config
        if scale == 0 or low >= high or cfg.closed_end_margin_motor_deg >= high - low:
            self._invalid('invalid motor mapping or limits')
            return None
        if not 0 <= now - received <= cfg.source_age_s + 1e-9:
            self._invalid('CAN source is stale or in the future')
            return None
        if self._last_now is not None and now < self._last_now:
            self._invalid('nonmonotonic control time')
            return None
        if self._last_received_at is not None:
            sample_dt = received - self._last_received_at
            if sample_dt < 0:
                self._invalid('nonmonotonic CAN time')
                return None
            if sample_dt > cfg.source_age_s + 1e-9:
                self._invalid('CAN sample gap')
                return None
        else:
            sample_dt = None
        self._last_now = now
        motor_deg = math.degrees(q)
        new_sample = sample_dt != 0
        if new_sample:
            if self._previous_motor_deg is None:
                # Seed from real reported speed instead of a fictional zero:
                # the first high-speed frame must not start contact dwell.
                self.estimated_velocity_rad_s = velocity
            else:
                measured = math.radians(motor_deg - self._previous_motor_deg) / sample_dt
                self.estimated_velocity_rad_s += sample_dt / (cfg.motion_filter_s + sample_dt) * (
                    measured - self.estimated_velocity_rad_s)
            self._previous_motor_deg = motor_deg
            self._last_received_at = received
        motor_sign = cfg.closing_sign * math.copysign(1., scale)
        closed_distance = motor_deg - low if motor_sign < 0 else high - motor_deg
        return motor_deg, motor_sign, closed_distance, motor_sign * torque, received, new_sample

    def _check_loss(self, motor_deg, motor_sign, closing_torque, received):
        cfg = self.config
        # Continued closure can also be a soft object compressing. Only
        # treat that motion as loss when the closing force has gone too.
        if (motor_sign * (motor_deg - self._contact_motor_deg) + 1e-9 >= cfg.drop_close_motor_deg
                and closing_torque <= cfg.release_torque_nm):
            self._free('object lost: gripper continued closing')
            return True
        if closing_torque <= cfg.release_torque_nm:
            if self._release_since is None:
                self._release_since = received
            if received - self._release_since + 1e-9 >= cfg.release_dwell_s:
                self._free('object lost: closing torque released')
                return True
        else:
            self._release_since = None
        return False

    def observe_gap(self, state, scale, limits, now):
        """Observe real object loss during a bounded Leader feedback gap.

        No Leader angle is accepted here. Existing hold may survive a short
        gap, but neither contact nor a fresh hold can be established. The
        caller still owns the Leader timeout and pauses follower targets.
        """
        if not self.config.enabled:
            self.reset()
            return self
        self._candidate_since = self._candidate_most_closed_leader_deg = None
        self._opening_since = None
        sample = self._sample(state, scale, limits, now)
        if sample is None:
            return self
        motor_deg, motor_sign, _, closing_torque, received, new_sample = sample
        if self.contact:
            if new_sample:
                self._check_loss(motor_deg, motor_sign, closing_torque, received)
        else:
            self.phase, self.reason = 'FREE', 'Leader feedback gap; waiting for fresh Leader'
        return self

    def step(self, leader_deg, commanded_motor_deg, state, scale, limits, now,
             *, leader_fresh=True):
        """Consume one checked snapshot before the next follower send.

        ``commanded_motor_deg`` is the *previous actual sent motor target*,
        including official direction/limit clipping. On contact it is retained
        as preload; substituting the actual motor position would drop grip.
        ``limits`` is the sorted (low, high) motor-angle range in degrees.
        Repeated CAN samples may release on fresh Leader opening, but cannot
        advance contact confirmation or force-loss confirmation.
        """
        if not self.config.enabled:
            self.reset()
            return self
        if leader_fresh is not True:
            return self._invalid('Leader sample is not fresh')
        if not all(_finite(v) for v in (leader_deg, commanded_motor_deg)):
            return self._invalid('non-finite Leader angle or target')
        cfg = self.config
        sample = self._sample(state, scale, limits, now)
        if sample is None:
            return self
        motor_deg, motor_sign, closed_distance, closing_torque, received, new_sample = sample
        if self.phase == 'INVALID':
            self.phase, self.reason = 'FREE', 'waiting for contact'

        sign = cfg.closing_sign
        contact_condition = (
            closed_distance > cfg.closed_end_margin_motor_deg
            and motor_sign * (commanded_motor_deg - motor_deg) >= cfg.error_motor_deg
            and closing_torque >= cfg.contact_torque_nm
            and abs(self.estimated_velocity_rad_s) <= cfg.max_speed_rad_s)

        free_opening = False
        if not self.hold:
            # Still cancel a pending new HOLD as soon as opening starts.
            candidate_reversal = min(.25, cfg.open_release_leader_deg)
            if self._candidate_open_peak_leader_deg is not None:
                if sign * (leader_deg - self._candidate_open_peak_leader_deg) < 0:
                    self._candidate_open_peak_leader_deg = leader_deg
                reclosing = sign * (leader_deg - self._candidate_open_peak_leader_deg)
                if reclosing + 1e-9 < candidate_reversal:
                    free_opening = True
                else:
                    self._candidate_open_peak_leader_deg = None
            elif self._candidate_since is not None:
                if sign * (leader_deg - self._candidate_most_closed_leader_deg) > 0:
                    self._candidate_most_closed_leader_deg = leader_deg
                opening = -sign * (leader_deg - self._candidate_most_closed_leader_deg)
                if opening + 1e-9 >= candidate_reversal:
                    self._candidate_open_peak_leader_deg = leader_deg
                    free_opening = True
            if free_opening:
                self._candidate_since = self._candidate_most_closed_leader_deg = None
                self.phase = 'OPENING' if self.contact else 'FREE'
                self.reason = ('Leader opening; hold released' if self.contact
                               else 'Leader opening; waiting for reclosure')
                contact_condition = False

        if self.contact:
            if self.hold:
                # Use this HOLD's entry angle, not a moving most-closed angle:
                # squeezing through finite HOLD and rebounding is not opening.
                opening = -sign * (leader_deg - self._hold_leader_deg)
                # SDK angles are float32 with 0.1-degree resolution.
                if opening + 1e-4 >= cfg.open_release_leader_deg:
                    if self._opening_since is None:
                        self._opening_since = now
                    if now - self._opening_since + 1e-9 >= cfg.open_release_dwell_s:
                        self.hold = False
                        self.phase, self.reason = 'OPENING', 'Leader opening; hold released'
                        self._open_peak_leader_deg = leader_deg
                        self._candidate_since = self._opening_since = None
                else:
                    self._opening_since = None
            else:
                if sign * (leader_deg - self._open_peak_leader_deg) < 0:
                    self._open_peak_leader_deg = leader_deg

        if not new_sample:
            # Neither a held torque sample nor elapsed wall time is evidence
            # of sustained contact or of an object falling out.
            return self
        if self.contact:
            if self._check_loss(motor_deg, motor_sign, closing_torque, received):
                return self
            if self.hold:
                return self
            # Opening is always free. Re-engagement needs a clear reversal
            # back to the original wall, plus a new contact confirmation.
            reclosing = sign * (leader_deg - self._open_peak_leader_deg)
            at_wall = sign * (leader_deg - self.wall_leader_deg) >= -1e-9
            contact_condition = (contact_condition and at_wall
                                 and reclosing + 1e-9 >= cfg.open_release_leader_deg)

        if not contact_condition:
            self._candidate_since = None
            self._candidate_most_closed_leader_deg = None
            if not self.contact:
                self.phase = 'FREE'
                if free_opening:
                    self.reason = 'Leader opening; waiting for reclosure'
                elif closed_distance <= cfg.closed_end_margin_motor_deg:
                    self.reason = 'closed end exclusion zone'
                elif abs(self.estimated_velocity_rad_s) > cfg.max_speed_rad_s:
                    self.reason = 'gripper moving too fast for contact confirmation'
                else:
                    self.reason = 'waiting for closing contact'
            return self

        if self._candidate_since is None:
            self._candidate_since = received
            self._candidate_most_closed_leader_deg = leader_deg
        if not self.contact:
            self.phase, self.reason = 'CONTACT_CANDIDATE', 'confirming closing contact'
        if received - self._candidate_since + 1e-9 < cfg.contact_dwell_s:
            return self
        if not self.contact:
            self.wall_leader_deg = leader_deg
            self.wall_target_leader_deg = commanded_motor_deg / scale
            self._contact_motor_deg = motor_deg
        self.contact = self.hold = True
        self.phase, self.reason = 'LOCKED', 'closing contact confirmed'
        self._hold_leader_deg = leader_deg
        self._opening_since = None
        self._open_peak_leader_deg = None
        self._candidate_since = self._release_since = None
        self._candidate_most_closed_leader_deg = self._candidate_open_peak_leader_deg = None
        return self

    def limit_target(self, leader_deg):
        """Limit only closure, keeping the original follower preload target."""
        if not _finite(leader_deg):
            raise ValueError('Leader target must be finite')
        if (self.config.enabled and self.contact
                and self.config.closing_sign * (leader_deg - self.wall_target_leader_deg) > 0):
            return self.wall_target_leader_deg
        return leader_deg

    def telemetry(self):
        return dict(enabled=self.config.enabled, phase=self.phase, reason=self.reason,
                    contact=self.contact, hold=self.hold, power_mw=self.power_mw,
                    estimated_velocity_rad_s=self.estimated_velocity_rad_s,
                    hold_leader_deg=self._hold_leader_deg,
                    wall_leader_deg=self.wall_leader_deg,
                    wall_target_leader_deg=self.wall_target_leader_deg)
