"""CAD frames on both solarian-gripper1 MJCFs.

``tcp`` is the tool center, expressed by ``tcp_from_flange``. ``camera`` sits
on the lens, which is where a wrist camera mounts.
"""

import numpy as np
import pytest


def _tcp_in_flange(mujoco, model):
    fid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "flange")
    tid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "tcp")
    assert fid >= 0 and tid >= 0
    assert model.site_bodyid[fid] == model.site_bodyid[tid]

    qinv = np.zeros(4)
    mujoco.mju_negQuat(qinv, np.asarray(model.site_quat[fid], dtype=float))
    pos = np.zeros(3)
    mujoco.mju_rotVecQuat(
        pos,
        np.asarray(model.site_pos[tid], dtype=float)
        - np.asarray(model.site_pos[fid], dtype=float),
        qinv,
    )
    quat = np.zeros(4)
    mujoco.mju_mulQuat(quat, qinv, np.asarray(model.site_quat[tid], dtype=float))
    if quat[0] < 0.0:
        quat = -quat
    return pos, quat


def _lens_holder_center(mujoco, model, data):
    for geom_id in range(model.ngeom):
        mesh_id = model.geom_dataid[geom_id]
        if mesh_id < 0 or model.geom_group[geom_id] != 2:
            continue
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_MESH, mesh_id) or ""
        if "lens_holder" not in name:
            continue
        adr = model.mesh_vertadr[mesh_id]
        count = model.mesh_vertnum[mesh_id]
        quat = model.geom_quat[geom_id]
        origin = data.geom_xpos[geom_id]
        total = np.zeros(3)
        for vert in model.mesh_vert[adr : adr + count]:
            rotated = np.zeros(3)
            mujoco.mju_rotVecQuat(rotated, vert, quat)
            total += rotated
        return total / count + origin
    raise AssertionError("MJCF has no lens_holder visual mesh")


@pytest.mark.parametrize(
    ("mjcf_attr", "module_path", "class_name", "dependency"),
    [
        (
            "MJCF_FEETECH_PATH",
            "solarian_gripper1.gripper_feetech",
            "Gripper1FeetechModule",
            "solarian_feetech",
        ),
        (
            "MJCF_ROBSTRIDE_PATH",
            "solarian_gripper1.gripper_robstride",
            "Gripper1RobstrideModule",
            "solarian_robstride",
        ),
    ],
)
def test_tcp_from_flange_matches_mjcf_sites(mjcf_attr, module_path, class_name, dependency):
    mujoco = pytest.importorskip("mujoco")
    pytest.importorskip(dependency)
    import importlib

    import solarian_gripper1

    module = importlib.import_module(module_path)
    model = mujoco.MjModel.from_xml_path(getattr(solarian_gripper1, mjcf_attr))
    pos, quat = _tcp_in_flange(mujoco, model)
    offset = getattr(module, class_name).tcp_from_flange
    assert pos == pytest.approx(offset.pos, abs=1e-6)
    assert quat == pytest.approx(offset.quat, abs=1e-6)


@pytest.mark.parametrize("mjcf_attr", ["MJCF_FEETECH_PATH", "MJCF_ROBSTRIDE_PATH"])
def test_camera_site_sits_on_the_lens(mjcf_attr):
    mujoco = pytest.importorskip("mujoco")
    import solarian_gripper1

    model = mujoco.MjModel.from_xml_path(getattr(solarian_gripper1, mjcf_attr))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    site_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "camera")
    assert site_id >= 0
    # The Feetech CAD frame is 4.7 mm from the lens-holder center. A frame
    # left on the rail (the Robstride export) is several centimetres away.
    center = _lens_holder_center(mujoco, model, data)
    assert np.linalg.norm(data.site_xpos[site_id] - center) < 0.006
