# Build a character

1. Name the character and select a model. Use **Insert another character mesh** to search your converted character library or import a local Blender, FBX, GLB or OBJ. Multi-file glTF assets require a local path.
2. Select a Shin Budokai source character and animation. Use the textured **Mesh** preview to inspect the retarget, or **Skeleton** for the original motion. Drag to orbit, scroll to zoom, and scrub the timeline.
3. For one-move replacements, choose a readable VF action. The comparison card shows its input and current animation before assigning the new one. **Review/change** reopens an assignment; the restore arrow returns it to the template.
4. Save the recipe or export a new EF-12 character pack. Check the conversion report and test it in-game before treating it as finished.

# Create combo strings

1. In the library, select the animation for the first move.
2. Under **04 · Combo strings**, name the string, select its existing VF entry move, and click **Start string with selected move**.
3. Select another library animation and click **Add selected move as follow-up**. Repeat to extend the string.
4. Set each move's L/H/E input, optional direction, damage and hit frame. **Transition frame** and **Accept until frame** refer to the parent animation. They write the engine's shift, command-accept and cancel fields.
5. To branch, change **Follow after** to an earlier move. Branches from the same parent need different button/direction inputs. Loops are rejected. Removing a move removes its descendants.
6. Save/load recipes to retain strings. Export creates distinct actions and parent-linked command rows, including the branches. A single-move replacement and a string cannot own the same entry.

The entry retains its existing VF command. New follow-up inputs use engine A for L, B for H and Y for E; these are not physical controller labels. E can play a selected attack animation but does not create a projectile or consume Ki. The mesh preview shows one move, not the whole string. The inherited follow-up commands for the selected entry are replaced only in the exported pack; other entry routes remain.

Up to 16 strings and 24 moves per string are supported. Generated files include `builder_recipe.json`, `builder_report.json` and `combo_report.json` for review. AI logic is inherited and does not learn new routes.
