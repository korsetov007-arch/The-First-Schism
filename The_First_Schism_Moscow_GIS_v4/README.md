# The First Schism — Moscow GIS-based high-resolution map build

This is a **large-scale Moscow map asset pack** built from public geographic polygon data, replacing the previous schematic sector geometry with 107 real district polygons clipped to the MKAD. It is a stronger geographic base, but has not yet been launched in HOI4; the in-game map editor/log is the final compatibility test.

## Main files

- `map/provinces.bmp` — 3072×4096 24-bit RGB, unique colour per province.
- `map/definition.csv` — province ID/RGB lookup with matching land terrain values.
- `map/heightmap.bmp` — 8-bit grayscale; subtle relief is **synthetic**, not a measured elevation model.
- `map/rivers.bmp` — 8-bit indexed river layer with one-pixel orthogonal paths.
- `map/terrain.bmp` — 8-bit indexed visual terrain (`urban`, parks/forest, outer plains).
- `map/trees.bmp`, `map/cities.bmp` — matching-size indexed layers.
- `map/world_normal.bmp` — 24-bit RGB normal map derived from the relief layer.
- `map/default.map`, `map/positions.txt`, `map/continents.txt`, `map/adjacencies.csv` and `map/strategicregions/` — matching map metadata.
- `district_provinces.csv` — province-to-district ID lookup.
- `district_index.csv` — centroid coordinates and number of provinces per district ID.
- `preview/moscow_hoi4_map_preview.png` — cartographic preview.
- `preview/moscow_107_districts_index.png` — numbered district index.
- `preview/province_id_colours.png` — unique-colour diagnostic for the 906+ province raster.
- `tools/build_moscow_map_v3.py` and `tools/data/` — reproducible build script and compact source geometry.
- `integration/history/states/` — optional state templates; they all use `VOR` as a placeholder owner, so assign territory to the mod's factions before gameplay.

## Size and format checks

Dimensions: 3072×4096, both multiples of 256, 12,582,912 pixels total. This is below the commonly documented HOI4 map pixel-area ceiling. The generator confirms bitmap dimensions/modes, unique province colours, ID coverage, and consistency between province IDs, province definitions, positions, continent listing and strategic-region listing.

## Geography and limitations

The source is `karen07/moscow-geo` (`geojson/districts-in-mkad.geojson`), an open GeoJSON with 107 district polygons. Its derived features have empty property names, so they are labelled `001`–`107` in the index; these IDs follow source feature order and are not official names. The city-side polygons were kept in local geographic proportions and converted to a map raster without the hand-drawn radial-sector geometry of the earlier draft.

The Moscow River, Yauza, Setun, Skhodnya and Gorodnya are hand-traced approximate centre lines. Main road/rail lines are illustrative preview overlays, not road shapefile data. The grayscale heightmap is synthetic subtle relief because a verified DEM was not bundled with this source. Parks and forest shapes are approximations. Those layers need another production pass with authoritative OSM waterways/roads and a DEM for the highest fidelity.

## Integration warning

Do not copy these files over a working mod without a backup. Replacing the original 158-province European Russia map changes every province ID and geographic position. Existing `history/states`, strategic regions, country capitals, victory points, railways, supply nodes, airbases and focus/event references must be remapped. Example state files are separated under `integration/` and should only be installed after assigning each district to the intended clan/country tag.

## Source and license

District polygon data: `https://github.com/karen07/moscow-geo` (`geojson/districts-in-mkad.geojson`). The source repository README declares GNU Affero General Public License v3.0 (AGPL-3.0). The compact embedded geometry is a derived encoding of that source, not an independently surveyed map. Please review the source license and attribution before redistributing it as part of a mod.
