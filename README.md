# The First Schism — HOI4 mod

An original, fictional two-country starting map inspired by the supplied political-map reference. The opening bookmark is **1 January 1962**: Vortex and Ogorod control the Northern March. A hidden startup event begins an engine-managed civil war in Ogorod after one day. No divisions or custom interface are added.

## Install

Create `Documents\Paradox Interactive\Hearts of Iron IV\mod\The First Schism`. Copy the project contents into that folder, except for `The First Schism.mod`; copy that launcher descriptor one level up into the `mod` folder. Then enable **The First Schism** in the Paradox launcher. No external assets or dependencies are required.

## Regenerate map assets

From this folder, run `node tools\generate_map.js`. The generator is dependency-free and recreates the province, terrain, heightmap, river, flag and preview assets as well as the map and scenario definitions.

The hand-drawn preview is `preview\first_stage_map.svg`. The map files are a compact custom-map foundation and should be opened in HOI4 once to check compatibility with the installed game version.
