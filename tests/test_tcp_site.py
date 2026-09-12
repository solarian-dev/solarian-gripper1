"""The Feetech UMI-slim MJCF exports a CAD Frame named ``tcp``."""

import pytest


def test_feetech_mjcf_exports_tcp_site():
    mujoco = pytest.importorskip("mujoco")
    from solarian_umi_slim import MJCF_FEETECH_PATH

    model = mujoco.MjModel.from_xml_path(MJCF_FEETECH_PATH)
    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "tcp")
    assert sid >= 0, "umi_slim.xml must export a CAD Frame named 'tcp'"
    flange = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "flange")
    assert flange >= 0, "umi_slim.xml must export a CAD Frame named 'flange'"
