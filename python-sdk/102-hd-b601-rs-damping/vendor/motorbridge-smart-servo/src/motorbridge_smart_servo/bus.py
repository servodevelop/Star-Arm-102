from __future__ import annotations

from typing import Optional

from .fashionstar import FashionStarServo


class SmartServoBus:
    """Stable vendor-neutral entry point.

    New vendors should be added behind this factory while preserving the common
    bus methods: ping, scan, read_angle, monitor, and set_angle.
    """

    @classmethod
    def open(
        cls,
        *,
        vendor: str = "fashionstar",
        port: str,
        baudrate: int = 1_000_000,
        library_path: Optional[str] = None,
    ):
        key = vendor.strip().lower().replace("_", "-")
        if key in {"fashionstar", "fashion-star", "fs"}:
            return FashionStarServo(port, baudrate=baudrate, library_path=library_path)
        raise ValueError(f"unsupported smart-servo vendor: {vendor!r}")

