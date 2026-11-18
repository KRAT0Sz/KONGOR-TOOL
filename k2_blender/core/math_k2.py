"""
Mathematical structures and coordinate transformations for K2 Engine.
Follows math_inlines.h and k2_mathlib.h.
"""

import math
from typing import Tuple, Optional

class Matrix43:
    __slots__ = ("axis_x", "axis_y", "axis_z", "pos")

    def __init__(
        self,
        axis_x: Tuple[float, float, float] = (1.0, 0.0, 0.0),
        axis_y: Tuple[float, float, float] = (0.0, 1.0, 0.0),
        axis_z: Tuple[float, float, float] = (0.0, 0.0, 1.0),
        pos: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ):
        self.axis_x = axis_x
        self.axis_y = axis_y
        self.axis_z = axis_z
        self.pos = pos

    @classmethod
    def identity(cls) -> "Matrix43":
        return cls()

    @classmethod
    def from_translation(cls, x: float, y: float, z: float) -> "Matrix43":
        return cls(pos=(x, y, z))

    @classmethod
    def from_flat_floats(cls, f: Tuple[float, ...]) -> "Matrix43":
        if len(f) != 12:
            raise ValueError(f"Expected 12 floats for Matrix43, got {len(f)}")
        return cls(
            axis_x=(f[0], f[1], f[2]),
            axis_y=(f[3], f[4], f[5]),
            axis_z=(f[6], f[7], f[8]),
            pos=(f[9], f[10], f[11]),
        )

    def to_flat_floats(self) -> Tuple[float, ...]:
        return (
            self.axis_x[0], self.axis_x[1], self.axis_x[2],
            self.axis_y[0], self.axis_y[1], self.axis_y[2],
            self.axis_z[0], self.axis_z[1], self.axis_z[2],
            self.pos[0], self.pos[1], self.pos[2],
        )

    def transform_point(self, p: Tuple[float, float, float]) -> Tuple[float, float, float]:
        x, y, z = p
        return (
            x * self.axis_x[0] + y * self.axis_y[0] + z * self.axis_z[0] + self.pos[0],
            x * self.axis_x[1] + y * self.axis_y[1] + z * self.axis_z[1] + self.pos[1],
            x * self.axis_x[2] + y * self.axis_y[2] + z * self.axis_z[2] + self.pos[2],
        )

    def inverse(self) -> "Matrix43":
        # Transpose upper 3x3 rotation
        inv_x = (self.axis_x[0], self.axis_y[0], self.axis_z[0])
        inv_y = (self.axis_x[1], self.axis_y[1], self.axis_z[1])
        inv_z = (self.axis_x[2], self.axis_y[2], self.axis_z[2])
        
        # New translation: -inv_R * pos
        px, py, pz = self.pos
        new_px = -(px * inv_x[0] + py * inv_y[0] + pz * inv_z[0])
        new_py = -(px * inv_x[1] + py * inv_y[1] + pz * inv_z[1])
        new_pz = -(px * inv_x[2] + py * inv_y[2] + pz * inv_z[2])

        return Matrix43(inv_x, inv_y, inv_z, (new_px, new_py, new_pz))

def euler_yxz_to_quat(pitch_deg: float, roll_deg: float, yaw_deg: float) -> Tuple[float, float, float, float]:
    """
    K2 Euler ordering: YXZ convention (Roll around Y, Pitch around X, Yaw around Z).
    Right-handed coordinate system (math_inlines.h:417-437).
    """
    r_rad = math.radians(roll_deg) * 0.5
    p_rad = math.radians(pitch_deg) * 0.5
    y_rad = math.radians(yaw_deg) * 0.5

    sr = math.sin(r_rad)
    cr = math.cos(r_rad)
    sp = math.sin(p_rad)
    cp = math.cos(p_rad)
    sy = math.sin(y_rad)
    cy = math.cos(y_rad)

    qx = cy * sp * cr - sy * cp * sr
    qy = cy * cp * sr + sy * sp * cr
    qz = cy * sp * sr + sy * cp * cr
    qw = cy * cp * cr - sy * sp * sr

    return (qx, qy, qz, qw)

def quat_to_euler_yxz(qx: float, qy: float, qz: float, qw: float) -> Tuple[float, float, float]:
    """
    Exact analytical inverse of euler_yxz_to_quat and M_GetAxis (c_axis.h:99-110).
    Returns (pitch_deg, roll_deg, yaw_deg).
    """
    sp = 2.0 * (qy * qz + qw * qx)
    sp = max(-1.0, min(1.0, sp))
    pitch_rad = math.asin(sp)

    if abs(cos_p := math.cos(pitch_rad)) > 1e-6:
        yaw_rad = math.atan2(-(2.0 * (qx * qy - qw * qz)), 1.0 - 2.0 * (qx * qx + qz * qz))
        roll_rad = math.atan2(2.0 * (qw * qy - qx * qz), 1.0 - 2.0 * (qx * qx + qy * qy))
    else:
        # Gimbal lock: pitch is +/- 90 degrees
        yaw_rad = math.atan2(2.0 * (qx * qy + qw * qz), 1.0 - 2.0 * (qy * qy + qz * qz))
        roll_rad = 0.0

    return (math.degrees(pitch_rad), math.degrees(roll_rad), math.degrees(yaw_rad))

def calculate_tangent_sign(
    normal: Tuple[float, float, float],
    tangent: Tuple[float, float, float],
    bitangent: Tuple[float, float, float],
) -> int:
    """
    Calculates the sign byte (0 or 255) for the bitangent parity.
    cross(normal, tangent) . bitangent
    """
    nx, ny, nz = normal
    tx, ty, tz = tangent
    # Cross product
    cx = ny * tz - nz * ty
    cy = nz * tx - nx * tz
    cz = nx * ty - ny * tx
    # Dot with bitangent
    bx, by, bz = bitangent
    dot = cx * bx + cy * by + cz * bz
    return 0 if dot >= 0.0 else 255

class BoundingBox:
    __slots__ = ("bmin", "bmax")

    def __init__(self, bmin: Optional[Tuple[float, float, float]] = None, bmax: Optional[Tuple[float, float, float]] = None):
        self.bmin = bmin or (float("inf"), float("inf"), float("inf"))
        self.bmax = bmax or (float("-inf"), float("-inf"), float("-inf"))

    def is_empty(self) -> bool:
        return self.bmin[0] > self.bmax[0]

    def add_point(self, p: Tuple[float, float, float]) -> None:
        self.bmin = (
            min(self.bmin[0], p[0]),
            min(self.bmin[1], p[1]),
            min(self.bmin[2], p[2]),
        )
        self.bmax = (
            max(self.bmax[0], p[0]),
            max(self.bmax[1], p[1]),
            max(self.bmax[2], p[2]),
        )
