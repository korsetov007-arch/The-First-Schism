# The First Schism — HOI4 mod

The project now uses a Moscow GIS-based map with 906 provinces, 108 states (107 city districts and one outer-belt state), and 108 strategic regions. The map assets and state templates are in `The_First_Schism_Moscow_GIS_v4`; MOS starts with 82 states; VOR holds 14 western districts and OGO 12 northern districts. The crisis chain lets OGO declare war or concede three districts; the Dark Watch forms after a coup if concessions continue.

## Edit the map

1. Download and extract the Windows x64 release of [HOI4 Map Editor](https://github.com/AdriianCOE/HOI4-Map-Editor/releases).
2. In the editor, choose **File → Open HOI4 Mod...** and select this project folder.
3. Edit provinces and states, then use **Save Project** to apply the validated changes.

The editor uses `map\provinces.bmp` and `map\definition.csv` for province editing, and `history\states\*.txt` for the States workspace. Keep an independent backup before editing.

## Install in Hearts of Iron IV

In the Paradox launcher, create a local mod named **The First Schism**. Copy the project contents into the folder created by the launcher, keeping the launcher's generated `.mod` file in the parent `mod` folder so its path points to the installed folder. Then enable **The First Schism** in the launcher. Do not copy the repository's `The First Schism.mod`: its relative path is not portable across installations and can leave the mod listed in the launcher without loading its files in-game.

## Map source

The district geometry is derived from `karen07/moscow-geo` (`geojson/districts-in-mkad.geojson`), whose repository declares AGPL-3.0. The pack's `README.md` and `tools\data\SOURCE_ATTRIBUTION.txt` document the source and limitations. Rivers, terrain, and relief are approximate; verify the map in the target HOI4 version before gameplay.


## Rebuild starting state ownership

Run `python tools/build_moscow_scenario.py` from the project folder to regenerate all 108 Moscow state-history files from the GIS province/district mapping. The script validates that province IDs 1–906 are unique and assigns 82 states to the Moscow Administration, 14 to Vortex, and 12 to Ogorod.
