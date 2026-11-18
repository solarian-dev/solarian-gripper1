#!/usr/bin/env bash
# Regenerate everything derived from the Onshape export in ./cad:
#   STL/Individual (print-oriented parts), STL/Plates, docs/media stills and assembly videos.
# Needs: python3 + numpy + pillow, node + playwright (Chromium/Chrome with WebGL), ffmpeg.
set -euo pipefail
cd "$(dirname "$0")"
python3 prep.py cad/meshes data
python3 fasteners.py
# print orientation: auto-picked, with the right finger holder forced to mirror the left one
python3 orient.py rack feetech_gripper_holder finger_holder_left_n finger_holder_right_n:1,0,0 soft_gripper_finger \
  crank link-1 link-2 feetech_back_holder_to_horn horn_spacer_3.5_mm feetech_camera_mount_bottom camera_holder_v3
python3 plates.py ../../STL/Plates
python3 anim.py
for s in $(python3 -c "import json;print(' '.join(x['name'] for x in json.load(open('steps.json'))))"); do
  node render.mjs "shots_$s.json" "frames/$s" 1280 720
done
python3 encode.py frames ../../docs/media/assembly
python3 stills.py && node render.mjs stills.json stills 1600 1000
