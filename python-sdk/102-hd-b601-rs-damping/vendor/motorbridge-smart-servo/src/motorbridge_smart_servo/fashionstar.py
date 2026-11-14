from __future__ import annotations

import time
from pathlib import Path
from typing import Iterator, Optional

from ._native import AngleSample, ServoMonitor
from ._native import FashionStarServo as _NativeFashionStarServo


class SmartServoError(RuntimeError):
    """Base exception raised by motorbridge-smart-servo."""


class LibraryLoadError(SmartServoError):
    """Kept for source compatibility; PyO3 wheels do not load an external DLL."""


class ServoBusError(SmartServoError):
    """Raised when a native bus operation fails."""


def _wrap_native_error(exc: RuntimeError) -> ServoBusError:
    return ServoBusError(str(exc))


class FashionStarServo:
    """FashionStar UART smart-servo bus.

    The Python API is intentionally vendor-stable. The implementation underneath
    is a PyO3 native extension, so wheels contain the Rust core directly instead
    of loading a separate smart_servo_abi DLL/SO with ctypes.
    """

    def __init__(
        self, port: str, baudrate: int = 1_000_000, library_path: Optional[str] = None
    ):
        if library_path is not None:
            # Keep the old constructor shape compatible, but the new PyO3 backend
            # no longer needs or honors an external native-library path.
            raise LibraryLoadError("library_path is not supported by the PyO3 backend")
        self.port = port
        self.baudrate = baudrate
        try:
            self._inner = _NativeFashionStarServo(port, baudrate)
        except RuntimeError as exc:
            raise _wrap_native_error(exc) from exc

    @property
    def is_open(self) -> bool:
        return bool(self._inner.is_open)

    def close(self) -> None:
        try:
            self._inner.close()
        except RuntimeError as exc:
            raise _wrap_native_error(exc) from exc

    def __enter__(self) -> "FashionStarServo":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    @staticmethod
    def _check_id(servo_id: int) -> int:
        if not 0 <= int(servo_id) <= 253:
            raise ValueError("servo_id must be in range 0..253")
        return int(servo_id)

    def ping(self, servo_id: int) -> bool:
        try:
            return bool(self._inner.ping(self._check_id(servo_id)))
        except RuntimeError as exc:
            raise _wrap_native_error(exc) from exc

    def scan(self, max_id: int = 253) -> list[int]:
        """Return online servo IDs in `0..max_id`."""
        try:
            return list(self._inner.scan(self._check_id(max_id)))
        except RuntimeError as exc:
            raise _wrap_native_error(exc) from exc

    def read_angle(self, servo_id: int, multi_turn: bool = True) -> AngleSample:
        """Read one angle sample.

        `raw_deg` is the protocol value read from the servo.
        `filtered_deg` suppresses power-cycle A->0->B glitches.
        `reliable=False` means `filtered_deg` is being held from the last good value.
        """
        try:
            return self._inner.read_angle(self._check_id(servo_id), bool(multi_turn))
        except RuntimeError as exc:
            raise _wrap_native_error(exc) from exc

    def read_raw_angle(self, servo_id: int, multi_turn: bool = True) -> float:
        return float(self.read_angle(servo_id, multi_turn=multi_turn).raw_deg)

    def read_filtered_angle(self, servo_id: int, multi_turn: bool = True) -> float:
        return float(self.read_angle(servo_id, multi_turn=multi_turn).filtered_deg)

    def monitor(
        self,
        servo_id: int,
        multi_turn: bool = True,
        interval_s: float = 0.02,
        count: Optional[int] = None,
    ) -> Iterator[AngleSample]:
        """Yield angle samples at a fixed interval without crashing on transient timeouts."""
        emitted = 0
        while count is None or emitted < count:
            try:
                yield self.read_angle(servo_id, multi_turn=multi_turn)
                emitted += 1
            except ServoBusError:
                if count is not None:
                    emitted += 1
            time.sleep(interval_s)

    def set_angle(
        self,
        servo_id: int,
        angle_deg: float,
        multi_turn: bool = False,
        interval_ms: int = 0,
    ) -> None:
        if interval_ms < 0:
            raise ValueError("interval_ms must be >= 0")
        try:
            self._inner.set_angle(
                self._check_id(servo_id),
                float(angle_deg),
                bool(multi_turn),
                int(interval_ms),
            )
        except ValueError:
            raise
        except RuntimeError as exc:
            raise _wrap_native_error(exc) from exc

    def reset_multi_turn(self, servo_id: int) -> None:
        try:
            self._inner.reset_multi_turn(self._check_id(servo_id))
        except RuntimeError as exc:
            raise _wrap_native_error(exc) from exc

    def set_origin_point(self, servo_id: int) -> None:
        try:
            self._inner.set_origin_point(self._check_id(servo_id))
        except RuntimeError as exc:
            raise _wrap_native_error(exc) from exc

    def set_damping(self, servo_id: int, power: int) -> None:
        """Send opcode 0x09 using this bus's existing native controller lock."""
        if type(servo_id) is not int or not 0 <= servo_id <= 253:
            raise ValueError("servo_id must be an integer in range 0..253")
        if type(power) is not int or not 0 <= power <= 65535:
            raise ValueError("power must be an integer in range 0..65535")
        try:
            self._inner.set_damping(servo_id, power)
        except RuntimeError as exc:
            raise _wrap_native_error(exc) from exc

    def set_stop_mode(self, servo_id: int, mode: int, power: int) -> None:
        try:
            self._inner.set_stop_mode(self._check_id(servo_id), int(mode), int(power))
        except RuntimeError as exc:
            raise _wrap_native_error(exc) from exc

    def set_zero_confirm_samples(self, samples: int) -> int:
        """Set zero-jump confirmation count; return previous value (RS local fix)."""
        if type(samples) is not int or not 1 <= samples <= 65535:
            raise ValueError("samples must be an integer within 1..65535")
        try:
            return int(self._inner.set_zero_confirm_samples(samples))
        except RuntimeError as exc:
            raise _wrap_native_error(exc) from exc

    def set_loss_threshold(self, threshold: int) -> None:
        """Set how many consecutive missed responses trigger a ServoBusError.
        A value of 0 disables the check (default is 20).
        """
        try:
            self._inner.set_loss_threshold(int(threshold))
        except RuntimeError as exc:
            raise _wrap_native_error(exc) from exc

    def sync_monitor(self, servo_ids: list[int]) -> dict[int, ServoMonitor | None]:
        """Query monitor data for multiple servos in one sync command (code 25).

        Returns a dict mapping servo_id -> ServoMonitor for every queried servo:
        - reliable=True: fresh reading from the servo this cycle.
        - reliable=False: servo did not respond; angle and telemetry are held
          from the last known good reading.
        - None: servo has never responded (no cached value available yet).

        Raises ServoBusError if any servo exceeds the consecutive loss threshold.
        """
        try:
            return self._inner.sync_monitor([self._check_id(i) for i in servo_ids])
        except RuntimeError as exc:
            raise _wrap_native_error(exc) from exc

    def unlock(self, servo_id: int) -> None:
        """Unlock the servo (set to stop mode unloaded)."""
        self.set_stop_mode(servo_id, mode=0x10, power=0)

    move_to = set_angle

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass


def list_library_candidates() -> list[Path]:
    """Return an empty list because PyO3 wheels do not use external native libraries."""
    return []
