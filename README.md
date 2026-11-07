# The First Schism — HOI4 mod

The project contains a 2048 × 1024 map of European Russia, with 158 province IDs (34 sea and 124 land). Its map assets come from `first_schism_european_russia_bmp_pack`; the pack is kept in the project as the original source copy. The existing 12 state definitions use the province IDs from this map.

## Edit the map

1. Download and extract the Windows x64 release of [HOI4 Map Editor](https://github.com/AdriianCOE/HOI4-Map-Editor/releases).
2. In the editor, choose **File → Open HOI4 Mod...** and select this project folder.
3. Edit provinces and states, then use **Save Project** to apply the validated changes.

The editor uses `map\provinces.bmp` and `map\definition.csv` for province editing, and `history\states\*.txt` for the States workspace. Keep an independent backup before editing.

## Install in Hearts of Iron IV

Copy the project folder to `Documents\Paradox Interactive\Hearts of Iron IV\mod\The First Schism`. Copy `The First Schism.mod` to the parent `mod` folder, then enable **The First Schism** in the Paradox launcher.

The old procedural map generator has been removed so it cannot overwrite the European Russia map.
