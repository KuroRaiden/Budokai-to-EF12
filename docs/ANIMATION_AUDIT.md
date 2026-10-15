# Animation audit and shared retargeting fixes

The animation library remains experimental. A valid decoded clip is not the same as a polished fighting animation.

## Source checks

The local source audit sampled every frame of the 5,528 selectable clips across 25 source-character groups. It found no decoder exceptions or non-finite skeleton positions in that set. Other AMM bank layouts remain unsupported and were not included. Game files and raw motion samples are not distributed with this report.

## Corrected shared behavior

- The old retargeter pinned the lower toe to its bind-floor height on every frame. It now retains the source animation's toe clearance, scaled to the selected character. This preserves airborne movement instead of flattening it.
- Horizontal movement now uses a median of matching limb-length ratios instead of a fixed 1.30 factor. The tested Goku starter calibrates to approximately 1.00; the tested Vegeta import calibrates to approximately 1.11.
- Compatible Euler branches, continuous angle values and linear sampled curves reduce spurious rotation flips. They cannot eliminate genuine abrupt source poses.
- Unnecessary dependency updates for unmapped bones were removed from baking.
- Mesh preview cache keys include the retargeter and helper contents. Previously generated previews regenerate after an algorithm change.
- The optional **Follow movement** camera tracks the posed mesh to keep translating and airborne motions visible.

## Retarget checks

Twelve clips were baked in Blender: Goku indices 0, 17, 29, 15, 37, 83 and 124; Vegeta indices 0, 12, 14, 33 and 41. These include idle, punches, kicks and airborne/cinematic motions. Examples of retained maximum lower-toe clearance, in target scene units:

| Clip | Previous forced clearance | Revised clearance |
| --- | ---: | ---: |
| Goku 37 | 0 | 11.39 |
| Goku 83 | 0 | 22.39 |
| Vegeta 33 | 0 | 13.73 |

These measurements describe the intended mapped joint trajectory. They do not establish correct mesh volume, sole contact, game collisions or combat behavior. Each conversion bank now writes `retarget_quality.json` with scale, height and rotation-continuity diagnostics. The source-only regression suite also covers proportional scale, ground/air clearance, Euler wrapping and cache invalidation.

## Still needs work

Finger posing, foot-contact cleanup, extreme poses, individual skeleton proportions, collision timing and in-game behavior need further review. Only the two target models above were used for the representative retarget batch; other characters are not declared visually validated. Whole-string playback is not simulated by the preview. Re-export old character packs to apply corrections; existing exported files are preserved.
