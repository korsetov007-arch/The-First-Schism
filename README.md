# The First Schism — HOI4 mod

The project now uses a Moscow GIS-based map with 906 provinces, 108 states (107 city districts and one outer-belt state), and 108 strategic regions. The map assets and state templates are in `The_First_Schism_Moscow_GIS_v4`; district ownership is temporarily assigned to VOR.

## Edit the map

1. Download and extract the Windows x64 release of [HOI4 Map Editor](https://github.com/AdriianCOE/HOI4-Map-Editor/releases).
2. In the editor, choose **File → Open HOI4 Mod...** and select this project folder.
3. Edit provinces and states, then use **Save Project** to apply the validated changes.

The editor uses `map\provinces.bmp` and `map\definition.csv` for province editing, and `history\states\*.txt` for the States workspace. Keep an independent backup before editing.

## Install in Hearts of Iron IV

Copy the project folder to `Documents\Paradox Interactive\Hearts of Iron IV\mod\The First Schism`. Copy `The First Schism.mod` to the parent `mod` folder, then enable **The First Schism** in the Paradox launcher.

## Map source

The district geometry is derived from `karen07/moscow-geo` (`geojson/districts-in-mkad.geojson`), whose repository declares AGPL-3.0. The pack's `README.md` and `tools\data\SOURCE_ATTRIBUTION.txt` document the source and limitations. Rivers, terrain, and relief are approximate; verify the map in the target HOI4 version before gameplay.
