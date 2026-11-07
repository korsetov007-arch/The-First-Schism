# The First Schism — HOI4 mod

A fictional HOI4 scenario set across an enlarged version of European Russia. The lore countries remain fictional: Vortex (Вихрь), Ogorod (Огород), and the other factions represented by the existing character and flag assets. The starting bookmark is **1 January 1962**.

## Install

1. Create `Documents\\Paradox Interactive\\Hearts of Iron IV\\mod\\The First Schism`.
2. Copy the project contents into that folder, except for `The First Schism.mod`; copy that launcher descriptor one level up into the `mod` folder.
3. Enable **The First Schism** in the Paradox launcher.

The playable mod uses the map assets already included under `map/`; **running a generator is not part of installation**. The BMPs, province definitions, state files, strategic regions, supply areas, and province positions must be kept in sync when the map is changed.

## Map status

The current regional map is an early large-scale layout pass, not a survey-accurate geographic conversion yet. The next map pass should replace the hand-authored outline and schematic rivers with aligned geographic data for the Baltic and White Seas, Lake Ladoga and Onega, the Volga and Don basins, the Caspian Sea, and the western Urals, while retaining the mod's fictional country borders and names.

Natural Earth publishes public-domain vector datasets suitable as a source for coastlines, lakes, and rivers: https://www.naturalearthdata.com/downloads/10m-physical-vectors/

The preview is `preview/first_stage_map.svg`. Always validate province colors, map dimensions, state ownership, and the map in the target HOI4 version before treating a map revision as release-ready.
