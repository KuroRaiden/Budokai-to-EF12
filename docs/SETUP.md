# Local workspace setup

The source release packages an existing experimental conversion workflow. It does not extract ROMs or build all reference assets from scratch. You need your own extracted animation/model library, a prepared character template, and the following local toolchain.

## Prerequisites

- Windows, Python 3.10+ and Pillow.
- Blender 4.0.2 for mesh preparation and retargeting; Blender 2.67b for the legacy EF-12 exporters. Export scripts depend on these APIs.
- EF-12 creator tools: ConvXSI2FMOT, ConvDAE2FMDL, conversion CSV settings, Blender motion/model exporters and G6Lite reference rigs.
- A prepared VF-Montauk Speed template with one 3D style and compatible starter model.

No vendor binaries, exporter add-ons, game content or keys are included in the repository. Do not place them in tracked folders.

## Directory contract

Set `workspace` to a local directory containing:

```text
work/
  blender/blender-4.0.2-windows-x64/blender.exe
  blender_pillow/PIL/                         # Pillow for Blender 4's Python
  ef12/
    blender_legacy/<Blender folder>/blender.exe
    converter_new/ConvXSI2FMOT.exe
    converter_new/ConvDAE2FMDL.exe
    converter_new/ConvMotion.csv
    converter_new/ConvModel.csv
    motion_exporter/ef12_motion_export/...
    model_exporter/ef12_model_export/...
    G6Lite_Rig/G6Lite_Rig/G6Lite_Rig.blend
    blenderSample/blenderSample/Skeleton/G6Lite_SKL_BL.blend
    rig_inspection.json
    pilot_v2/Goku_geometry.json
    pilot_v2/source_bind.json
    pilot_v2/Goku_EF12_G6Lite.blend
    pilot_v2/toon_ramp.tga
    pilot_v2/toon_diffuse_sphere.tga
    pilot_v2/toon_black.tga
    pilot_v2/<starter textures>
outputs/
  Goku_Corrected_Review.blend
```

`--install-pipeline` copies the repository's `pipeline/*.py` scripts into `workspace/work/ef12`; previous files are backed up in `before_budokai_to_ef12`. It does not install vendor tools or generate missing reference data. Scripts read `DBZ_WORKSPACE`; model import passes `STUDIO_MODEL_SOURCE` and `STUDIO_MODEL_DIR`.

`rig_inspection.json` describes source and target armatures (`armatures[].bones`, object matrices). `pipeline/inspect_rigs.py` can generate it from your own local source character and reference rig after you set its local source path. The prepared starter geometry and corrected review blend must already exist; these are not supplied by this source release. `pipeline/` includes their preparation/export scripts for rebuilding a compatible workspace.

The `assets` directory you configure must contain the extracted `animations/`, `models/`, `skeletons/` and `support/` trees. The `template` folder needs `character.ini`, `mth/MotHead-1.csv`, the skeleton, model, collision, motion, effect and portrait resources of your prepared VF character. This is a dependency on a prepared local character pack, not an empty stock game directory.

Run `python configure.py` with the paths shown in the README, or import an existing local configuration with `--from-config`. Configuration generates the default web mesh preview from your local prepared geometry. `config.json` and generated media stay ignored by Git.

For diagnostics, inspect local `PreviewCache/*/preview.log`, `Models/*/native/import.log` and `Characters/*/conversion/*/conversion.log`. These can include local paths and should be reviewed before sharing.

## Known limits

- Other AMM layouts are counted as unsupported and omitted.
- Imported models need the supported named humanoid bones for animation/export. Arbitrary meshes are not automatically rigged.
- Hit timing defaults are estimates; collision parts inherit copied VF attack defaults.
- Generated combo command timing follows the template format and needs in-game validation.
- Export creates a new folder; installing it and registering a character in EF-12 are manual steps.
