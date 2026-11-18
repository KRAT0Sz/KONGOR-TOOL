import math
import pytest
from k2_blender.core.math_k2 import (
    Matrix43,
    euler_yxz_to_quat,
    quat_to_euler_yxz,
    calculate_tangent_sign,
    BoundingBox
)

def test_euler_yxz_to_quat_and_back():
    # Test identity rotation
    qx, qy, qz, qw = euler_yxz_to_quat(0.0, 0.0, 0.0)
    assert pytest.approx(qx, abs=1e-5) == 0.0
    assert pytest.approx(qy, abs=1e-5) == 0.0
    assert pytest.approx(qz, abs=1e-5) == 0.0
    assert pytest.approx(qw, abs=1e-5) == 1.0

    pitch, roll, yaw = quat_to_euler_yxz(0.0, 0.0, 0.0, 1.0)
    assert pytest.approx(pitch, abs=1e-4) == 0.0
    assert pytest.approx(roll, abs=1e-4) == 0.0
    assert pytest.approx(yaw, abs=1e-4) == 0.0

    # Test 90-degree pitch
    qx, qy, qz, qw = euler_yxz_to_quat(90.0, 0.0, 0.0)
    p, r, y = quat_to_euler_yxz(qx, qy, qz, qw)
    assert pytest.approx(p, abs=1e-3) == 90.0
    assert pytest.approx(r, abs=1e-3) == 0.0
    assert pytest.approx(y, abs=1e-3) == 0.0

    # Test combined angles
    orig_p, orig_r, orig_y = 25.0, -15.0, 40.0
    qx, qy, qz, qw = euler_yxz_to_quat(orig_p, orig_r, orig_y)
    p, r, y = quat_to_euler_yxz(qx, qy, qz, qw)
    assert pytest.approx(p, abs=1e-3) == orig_p
    assert pytest.approx(r, abs=1e-3) == orig_r
    assert pytest.approx(y, abs=1e-3) == orig_y

def test_matrix43_identity_and_transform():
    mat = Matrix43.identity()
    point = (3.0, 5.0, -7.0)
    transformed = mat.transform_point(point)
    assert pytest.approx(transformed[0]) == 3.0
    assert pytest.approx(transformed[1]) == 5.0
    assert pytest.approx(transformed[2]) == -7.0

def test_matrix43_translation():
    mat = Matrix43.from_translation(10.0, -5.0, 2.0)
    res = mat.transform_point((1.0, 2.0, 3.0))
    assert pytest.approx(res[0]) == 11.0
    assert pytest.approx(res[1]) == -3.0
    assert pytest.approx(res[2]) == 5.0

def test_matrix43_invert():
    mat = Matrix43(
        axis_x=(1.0, 0.0, 0.0),
        axis_y=(0.0, 0.0, 1.0),
        axis_z=(0.0, -1.0, 0.0),
        pos=(5.0, 10.0, 15.0)
    )
    inv = mat.inverse()
    p = (2.0, 3.0, 4.0)
    p_trans = mat.transform_point(p)
    p_back = inv.transform_point(p_trans)
    assert pytest.approx(p_back[0], abs=1e-4) == p[0]
    assert pytest.approx(p_back[1], abs=1e-4) == p[1]
    assert pytest.approx(p_back[2], abs=1e-4) == p[2]

def test_calculate_tangent_sign():
    normal = (0.0, 0.0, 1.0)
    tangent = (1.0, 0.0, 0.0)
    bitangent = (0.0, 1.0, 0.0) # normal x tangent = (0, 1, 0), so dot > 0 -> sign = 0 (positive)
    sign = calculate_tangent_sign(normal, tangent, bitangent)
    assert sign == 0

    neg_bitangent = (0.0, -1.0, 0.0)
    sign_neg = calculate_tangent_sign(normal, tangent, neg_bitangent)
    assert sign_neg == 255 # negative sign byte in K2

def test_bounding_box():
    bb = BoundingBox()
    assert bb.is_empty()
    bb.add_point((-2.0, 5.0, 1.0))
    bb.add_point((3.0, -4.0, 10.0))
    assert bb.bmin == (-2.0, -4.0, 1.0)
    assert bb.bmax == (3.0, 5.0, 10.0)
