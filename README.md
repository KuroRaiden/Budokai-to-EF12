# Budokai-to-EF12

A local Windows character and combo editor for building **EF-12 VF 3D** characters from your own extracted **Shin Budokai: Another Road** motion library.

**[Project website](https://kuroraiden.github.io/Budokai-to-EF12/)** · **[Setup guide](docs/SETUP.md)** · **[Using the editor](docs/USAGE.md)**

## What it does

- Browse supported AMM clips, with original input labels where available.
- Preview the source skeleton or the textured character mesh with retargeted animation.
- Identify VF actions by readable names and their command inputs before replacing them.
- Import Blender, FBX, GLB/glTF or OBJ character meshes. Compatible named humanoid rigs support animation and native export; other rigs require mapping.
- Create combo strings and branches, edit follow-up timing, damage and hit frames, and save/load JSON recipes.
- Export native FMOT animations, FMDL models for compatible imports, and updated MTH/CMH command headers into a new character pack.

## Status

**Experimental source release, not a standalone converter installer.** The editor needs a prepared local VF template, rig resources, a converted starter mesh and a separately installed Blender/EF-12 toolchain. Those files are not distributed here. The setup guide documents the current workspace contract.

Combo generation has passed structural tests and native export checks. In-game combo behavior, timings and collision tuning still require playtesting. The mesh preview plays one clip at a time; it does not simulate command processing or an entire combo string. AI scripts remain inherited.

Only the **VF 3D** template is used. Follow-up L/H/E inputs compile to EF-12 engine A/B/Y. The requested L/H/G/E plus separate RB charge layout is stored as a design, but physical controller remapping and Ki charge logic are not generated. E does not generate beam effects, projectiles, resource costs or sounds. Unassigned actions retain the template behavior.

## Run locally

With Python 3.10+ and a prepared workspace:

```powershell
python -m pip install -r requirements.txt
python configure.py --assets "C:/LocalAssets/Shin_Budokai_Another_Road_Assets" --template "C:/LocalAssets/EF12_Characters/DBZ-Goku-VF" --workspace "C:/EF12Workspace" --install-pipeline
python studio.py
```

If you already use the local Studio, reuse its private configuration:

```powershell
python configure.py --from-config "C:/YourLocalStudio/config.json"
python studio.py
```

Open `http://127.0.0.1:8765`. The server binds to loopback and runs offline. **GitHub Pages hosts documentation, not the Python/Blender converter.**

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests use synthetic command headers; no game files are required. Native conversion needs the local resources described in the setup guide.

## Included and excluded

This repository contains editor code, our pipeline scripts, documentation, tests and a starter recipe containing clip references. It does **not** contain game models, textures, animations, ROMs, Switch/PSP archives, keys, generated character packs, Blender binaries, EF-12 converters or vendor exporters. Local configuration, caches and generated assets are ignored by Git.

See [NOTICE.md](NOTICE.md) for format references and third-party resource notes. This project is unofficial and is not affiliated with the game developers or publishers.
