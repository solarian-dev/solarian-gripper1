"""The Feetech solarian-gripper1 MJCF exports a CAD Frame named ``tcp``."""

import numpy as np
import pytest


def test_feetech_mjcf_exports_tcp_site():
    mujoco = pytest.importorskip("mujoco")
    from solarian_gripper_1 import MJCF_FEETECH_PATH

    model = mujoco.MjModel.from_xml_path(MJCF_FEETECH_PATH)
    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "tcp")
    assert sid >= 0, "gripper1.xml must export a CAD Frame named 'tcp'"
    flange = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "flange")
    assert flange >= 0, "gripper1.xml must export a CAD Frame named 'flange'"


def test_tcp_from_flange_matches_mjcf_sites():
    mujoco = pytest.importorskip("mujoco")
    from solarian_gripper_1 import MJCF_FEETECH_PATH
    from solarian_gripper_1.gripper_feetech import Gripper1FeetechModule

    model = mujoco.MjModel.from_xml_path(MJCF_FEETECH_PATH)
    fid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "flange")
    tid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "tcp")
    assert model.site_bodyid[fid] == model.site_bodyid[tid]

    pos_f = np.asarray(model.site_pos[fid], dtype=float)
    quat_f = np.asarray(model.site_quat[fid], dtype=float)
    pos_t = np.asarray(model.site_pos[tid], dtype=float)
    quat_t = np.asarray(model.site_quat[tid], dtype=float)

    qinv = np.zeros(4)
    mujoco.mju_negQuat(qinv, quat_f)
    delta_parent = pos_t - pos_f
    pos = np.zeros(3)
    mujoco.mju_rotVecQuat(pos, delta_parent, qinv)
    quat = np.zeros(4)
    mujoco.mju_mulQuat(quat, qinv, quat_t)
    if quat[0] < 0.0:
        quat = -quat

    offset = Gripper1FeetechModule.tcp_from_flange
    assert pos == pytest.approx(offset.pos, abs=1e-6)
    assert quat == pytest.approx(offset.quat, abs=1e-6)
