# assembly_render

Scripts that turn the Onshape assembly into the build assets in this repo:

- `STL/Individual/*.stl`: each printed part, rotated onto its best face for printing
- `STL/Plates/*.stl`: all PLA parts on one 220 × 220 mm plate, and the two TPU fingers
- `docs/media/assembly/*.mp4|webp`: the step-by-step assembly animations
- `docs/media/*.png`: hero, exploded and plate renders

Everything is rendered headless with WebGL in Chromium, so no Blender or GPU is needed.

## 1. Export from Onshape

Open the `solarian-gripper1` Onshape document while signed in, open the
browser devtools console, paste [`onshape_export.js`](onshape_export.js) and
run `await exportGripper()`. It downloads
`solarian-gripper1-onshape-export.zip` with:

| File | What |
| --- | --- |
| `assembly_gripper1_v5.json` | assembly definition of `gripper1_v5` (occurrence transforms + mates) |
| `assembly_feetech_raspberry_slim.json` | the assembly that also has the crank, links and servo horn |
| `meshes/*.stl` | each part tessellated in its part-studio frame (mm), 3° / 10 µm for printed parts |
| `solarian-gripper1.step` | STEP of `gripper1_v5` (copy it to `STEP/`) |

Unzip it into `cad/`, replacing what's there. Update the element IDs at the
top of `onshape_export.js` if the assemblies are renamed or recreated.

## 2. Build

```bash
cd tools/assembly_render
./build.sh
```

Requirements: Python 3 with `numpy` and `pillow`, Node with `playwright`
(Chrome or Chromium with WebGL via SwiftShader is fine), and `ffmpeg` with
`libx264` and `libwebp`.

## How it works

| File | Role |
| --- | --- |
| `prep.py` | Loads STLs, writes vertex/normal buffers (`data/*.tri`) and outline edges (`data/*.edg`, B-rep face boundaries + creases > 35°). |
| `scene.py` | Places every part from the Onshape occurrence transforms. The drive linkage (crank, links, horn) comes from the second assembly and is re-based on the shared `rack`. |
| `kin.py` | Crank-slider kinematics: given the closing travel `q` (mm, same as the MJCF `left_manifold_to_rail` joint), solves the crank angle and posts the links, carriages and fingers. |
| `fasteners.py` | Procedural socket-head and countersunk screws, nuts, heat-set inserts and the soldering iron (the CAD has no fasteners). |
| `anim.py` | The build sequence: fastener positions, then per step which parts are already in, offset keyframes for what moves in (and from where), the carriage position and the camera path. Edit this to change the guide. |
| `viewer.html` + `render.mjs` | Minimal WebGL renderer (shaded + outlines, clipping plane) driven by Playwright; renders a JSON list of shots to PNGs. |
| `encode.py` | Adds step titles and encodes per-step MP4s, a full MP4 and 640 px animated WebP previews. |
| `orient.py` | Picks a print orientation per part (max bed contact, min overhang) and writes `STL/Individual`. Force a direction with `name:x,y,z`. |
| `plates.py` | Shelf-packs the oriented parts into plate STLs. |
| `stills.py` | Hero, back and exploded renders. |
