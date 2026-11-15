# solarian-gripper1

A parallel gripper module for the Solarian framework. Two fingers, one actuator;
you command it by the desired **finger aperture in millimetres** and the module
handles the conversion for both real hardware and simulation.

The plugin ships **two actuator variants** that share the same finger kinematics
and aperture command space:

| Variant | Module | Default config | MJCF |
| --- | --- | --- | --- |
| Feetech STS | `Gripper1FeetechModule` | `conf_gripper_feetech.yaml` | `assets/gripper1.xml` |
| Robstride L7 | `Gripper1RobstrideModule` | `conf_gripper_robstride.yaml` | `assets/gripper1_robstride.xml` |

## Installation

```bash
pip install solarian-gripper1             # Feetech variant
pip install "solarian-gripper1[hardware]" # plus the Feetech servo SDK, on the machine wired to the gripper
```

The Robstride variant needs `solarian-robstride`, which is not on PyPI yet.
Install it from source alongside the gripper:

```bash
pip install -e "plugins/solarian-robstride[hardware]"
pip install -e "plugins/solarian-gripper1[robstride]"
```

## How it works

- Each module exposes a single actuator (`gripper`), matching the single
  physical servo. It converts an aperture command (mm) into the servo's
  normalized command space and writes that. Each backend maps normalized → physical:
  - **Real**: normalized → servo counts via the actuator calibration.
  - **Sim**: normalized → both jaw joints. `sim_joint` is the left slide;
    `sim_followers` drives the right slide through its own exported limits.
- The URDF gives each jaw its own joint and actuator. One command opens and
  closes both because the same normalized value is mapped through each range.

## Regenerating the sim model

Each variant has its own CAD assembly. Export a URDF plus STL meshes from the CAD tool and import it:

```bash
solarian cad-import solarian_gripper1/assets/gripper1_description --urdf gripper.zip --density 522
solarian cad-import solarian_gripper1/assets/gripper1_robstride_description --urdf gripper.zip --density 522
```

The Feetech import writes `solarian_gripper1/assets/gripper1.xml`; the Robstride import writes `solarian_gripper1/assets/gripper1_robstride.xml`. Both jaw joints are actuators. `left_manifold_to_rail` runs `[0, 0.0545]` m (0 = fingers apart, 0.0545 = fingers together). `right_manifold_to_rail` runs the mirror, `[-0.0545, 0]`. One gripper command drives both through `sim_followers`.

## Using it in a robot

1. Attach the model in your robot's sim `SceneConfig`, with a `prefix` matching
   the one in the gripper yaml (`gripper/`):

```python
from solarian.sim import SceneConfig, ModuleAttachment
from solarian_gripper1 import MJCF_FEETECH_PATH as GRIPPER_MJCF
from solarian_gripper1.gripper_feetech import Gripper1FeetechModule

class MyRobot(Robot):
    is_sim = True
    gripper = Gripper1FeetechModule()

    scene = SceneConfig(
        attachments=[
            ModuleAttachment(
                module="gripper",
                # Loaded straight from the installed plugin (meshes resolve
                # relative to the MJCF) -- no need to copy the model into your
                # project, so there's a single source of truth.
                mjcf=GRIPPER_MJCF,
                parent_body="right/wrist_flange",   # the arm flange body
                prefix="gripper/",
            ),
        ],
    )
```

For the Robstride variant, import `Gripper1RobstrideModule` and
`MJCF_ROBSTRIDE_PATH` instead. The Feetech MJCF attaches at the `flange` site;
the Robstride MJCF attaches at the `base` site.

The Feetech MJCF exports CAD Frames as sites: `flange` (mate to the arm),
`camera` (wrist lens), and `tcp` (tool center point). Pass
`Gripper1FeetechModule.tcp_from_flange` to the arm as `ik_tcp` so IK tracks
the flange plus that CAD offset.

Site-mate example (solarian-arm1 and this gripper both export a `flange` Frame):

```python
ModuleAttachment(
    module="right_gripper",
    mjcf=GRIPPER_MJCF,
    parent_site="right/flange",
    child_site="flange",
    prefix="right_gripper/",
)
```

2. Copy the matching yaml (`conf_gripper_feetech.yaml` or
   `conf_gripper_robstride.yaml`) into your project's `conf/` and set the real
   `port`/`id`, then run `solarian calibrate` on the gripper: sweep the
   full closed↔open travel, then move to the **fully closed** pose when asked
   so `drive_mode` matches `aperture_closed_mm` / `aperture_open_mm`.

3. Run `solarian calibrate-gripper-ranges` and read a ruler at each stop. This
   records `aperture_table`, the measured aperture curve. Skipping it leaves the
   module interpolating a straight line between the two endpoints, which the
   linkage does not follow.

4. Command the gripper by aperture in mm — send a waypoint whose `gripper` value
   is the aperture (e.g. `85` = fully open, `0` = closed). Read the current
   aperture with `module.read_aperture()`.

## Configuration

Fields specific to both modules:

- `aperture_table` — ruler-measured `norm` / `aperture_mm` pairs written by
  `solarian calibrate-gripper-ranges`. When present it defines the travel and
  the mm ↔ normalized map, superseding the two endpoint fields below.
- `aperture_closed_mm` / `aperture_open_mm` — physical fingertip separation at
  the two ends of travel, used for a straight-line map until a table is
  measured. Keep them consistent with the servo calibration and the `sim:`
  joint range.
- `actuators.gripper.sim` — maps the servo to `gripper/left_manifold_to_rail`,
  `range_min: 0.0` / `range_max: 0.0545` (the joint limits), `drive_mode: 1` so
  normalized -100 = closed, 100 = open.
- `interpolator_type: scalar` — GripperModule interpolates aperture in mm.

## License

[Apache License 2.0](LICENSE). Copyright 2026 PrimaryKey Inc. Parts of the
mechanical design and meshes in `solarian_gripper1/assets/` are derived from
the [UMI Gripper](https://cad.onshape.com/documents/a8a98201374f5cc9c6538790)
and [UMI Soft Finger](https://cad.onshape.com/documents/c8d06048fc2e425772f2749c)
of the [Universal Manipulation Interface](https://umi-gripper.github.io/) (UMI)
project, and the Robstride L7 drive from RobStride's
[EDULITE_A3](https://github.com/RobStride/EDULITE_A3) (MIT), and modified; see
[NOTICE](NOTICE). solarian-gripper1 is not affiliated with, sponsored by, or
endorsed by UMI, its authors, Stanford University, Columbia University, Toyota
Research Institute or RobStride.

Solarian and the Solarian logo are trademarks of PrimaryKey Inc. See the [trademark policy](https://github.com/solarian-dev/solarian/blob/main/TRADEMARKS.md).
