"""Add leader hold behavior to two Star Arm 102 control pairs.

Reuse serial checks, initialization, filtering, follower commands, and worker
management from stararm102_dual.py. This file tracks automatic leader hold.
"""

from collections import deque
import struct
import sys
import time

import stararm102_dual as dual


class HoverState:
    """Track automatic hold state for one leader; each pair has an instance."""

    def __init__(self, pair_number):
        self.pair_number = pair_number  # Identify the pair in status messages.
        # Compare six arm joints only; gripper ID 6 does not trigger hold.
        self.last_angles = [0.0] * 6
        self.still_since = None  # Start of the quiet interval, if any.
        self.locked = False  # Whether a hold command has been sent.
        self.just_locked = False  # Capture raw angles on the first held frame.

    def reset(self, angles):
        """Clear automatic hold while the HD button controls the leader."""
        self.last_angles = angles[:6]
        self.still_since = None
        self.locked = False
        self.just_locked = False

    def update(self, leader, filtered):
        """Update hold state and send a leader hold or release when needed."""
        now = time.time()
        if self.locked:
            if self.just_locked:
                # Capture actual joint angles after sending the hold command.
                self.last_angles = [leader.servos[i].angle_monitor for i in range(6)]
                self.just_locked = False
            else:
                # Use raw feedback to avoid filter delay in release detection.
                difference = sum(abs(self.last_angles[i] - leader.servos[i].angle_monitor)
                                 for i in range(6))
                if difference > 5:  # Release above five degrees summed change.
                    leader.stop_on_control_mode(0xff, 0x10, 0x00)
                    self.locked = False
                    print(f"Pair {self.pair_number}: 自动悬停解锁指令已发送", flush=True)
            return

        # While unlocked, use filtered angles to detect continuous stillness.
        difference = sum(abs(self.last_angles[i] - filtered[i]) for i in range(6))
        self.last_angles = filtered[:6]
        if difference > 0.1:  # Restart the timer above 0.1 degrees per loop.
            self.still_since = None
        elif self.still_since is None:
            self.still_since = now
        elif now - self.still_since > 1.0:
            # Hold all six leader joints after more than one quiet second.
            self.locked = True
            self.just_locked = True
            leader.send_sync_servo_monitor(list(dual.SERVO_IDS))
            # Keep the original hold packet format and final field value.
            commands = [
                struct.pack("<BlLHHH", i, int(leader.servos[i].angle_monitor * 10),
                            100, 50, 50, int(65535 / 16))
                for i in range(6)
            ]
            leader.send_sync_multiturnanglebyinterval(14, 6, commands)
            print(f"Pair {self.pair_number}: 自动悬停锁定指令已发送", flush=True)


def run_hover_pair(args, number):
    """Control one pair and update automatic hold on its leader."""
    # Each pair has its own button configuration and filter window.
    button = (dual.ButtonState(getattr(args, f"leader_{number}_button_id"))
              if dual.button_enabled(args, number) else None)
    buffer = deque(maxlen=getattr(args, f"pair_{number}_filtered_size"))
    hover = HoverState(number)
    count, started = 0, time.time()
    with dual.open_pair(args, number) as (leader, follower):
        while True:
            # Keep the normal read, filter, and follower-command sequence.
            angles = dual.read_angles(leader, button.id if button else None)
            targets = dual.filtered_angles(buffer, angles)
            # Button hold takes precedence over automatic leader hold.
            if button:
                was_locked = button.locked
                manual_locked = button.update(leader)
                if manual_locked != was_locked:
                    state = "锁定" if manual_locked else "解锁"
                    print(f"Pair {number}: 按钮{state}指令已发送", flush=True)
                if manual_locked or was_locked:
                    # Restart the stillness timer when button hold is released.
                    hover.reset(targets)
                else:
                    hover.update(leader, targets)
            else:
                hover.update(leader, targets)
            dual.send_angles(follower, targets)
            time.sleep(0.001)  # Preserve the normal control-loop delay.
            count += 1
            now = time.time()
            if now - started >= 1.0:
                print(f"Pair {number} hover loop frequency: {count / (now - started):.2f} Hz",
                      flush=True)
                count, started = 0, now


if __name__ == "__main__":
    # Reuse normal-mode checks and workers, replacing only the pair runner.
    # The 60-sample default can be overridden for either pair.
    sys.exit(dual.main(pair_runner=run_hover_pair, default_filter=60))
