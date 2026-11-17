# CAD sources

Parametric models for two of the projects. They are the source for the STEP
files in `assets/files/`, the renders in `assets/images/projects/`, and the
drawing sheets in `assets/drawings/`. Nothing here runs on GitHub Pages — run
it locally and commit the outputs.

```
pip install cadquery bpy          # bpy only for render.py
python3 shower_chair.py           # -> out/*.stl + the STEP assembly
python3 render.py final           # -> renders/final-*.png   (Blender/Cycles)
python3 dispenser.py              # -> out_disp/*.stl + the STEP assembly
python3 drawings.py               # -> drawings/*.svg        (orthographic sheets)
```

- `shower_chair.py` — the powered transfer system. Millimetres, origin on the
  bathroom floor in the plane of the tub wall, tub side is +X.
- `render.py` — Cycles renders of that model, one named view per camera.
- `dispenser.py` — the stepwise-dosing dispenser, part by part, plus a
  cutaway copy of the housing for the section views.
- `drawings.py` — projects the dispenser into front/right/top and section
  views and lays them out on sheets with a title block.

Every view on a sheet is the FRONT projection of the model turned into place
first (`PRE` in `drawings.py`); that is what keeps the sheet's up direction
consistent, since the exporter lays the model's Z across the page.
