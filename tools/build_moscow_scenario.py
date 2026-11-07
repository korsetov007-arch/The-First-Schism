#!/usr/bin/env python3
"""Regenerate the Moscow state history files from the GIS province-to-district mapping.

Run from any working directory:
    python tools/build_moscow_scenario.py

The script intentionally updates only history/states/*-moscow.txt. It does not
modify the province raster, country histories, focus trees, or event logic.
"""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIS = ROOT / "The_First_Schism_Moscow_GIS_v4"
DISTRICT_INDEX = GIS / "district_index.csv"
PROVINCE_INDEX = GIS / "district_provinces.csv"
STATE_DIR = ROOT / "history" / "states"

VOR_STATES = {1, 2, 5, 6, 7, 16, 17, 26, 27, 34, 35, 36, 78, 97}
OGO_STATES = {10, 11, 12, 19, 20, 21, 28, 29, 30, 31, 32, 33}
INDUSTRIAL_STATES = {
    8, 19, 21, 40, 41, 43, 44, 54, 55, 72, 84, 85, 86, 87,
    99, 100, 101, 102, 103, 104, 105, 106,
}
EXPECTED_PROVINCES = 906
EXPECTED_STATES = 108


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def owner_for(state_id: int) -> str:
    if state_id in VOR_STATES:
        return "VOR"
    if state_id in OGO_STATES:
        return "OGO"
    return "MOS"


def build() -> None:
    districts = {
        int(row["district_id"].removeprefix("D")): row
        for row in read_csv(DISTRICT_INDEX)
    }
    grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
    province_rows = read_csv(PROVINCE_INDEX)
    for row in province_rows:
        province_id = int(row["province_id"])
        state_id = int(row["district_id"])
        if not 1 <= province_id <= EXPECTED_PROVINCES:
            raise ValueError(f"Province ID out of range: {province_id}")
        grouped[state_id].append(row)

    if len(province_rows) != EXPECTED_PROVINCES:
        raise ValueError(f"Expected {EXPECTED_PROVINCES} provinces, got {len(province_rows)}")
    if len(grouped) != EXPECTED_STATES or set(grouped) != set(range(1, EXPECTED_STATES + 1)):
        raise ValueError(f"Expected states 1–{EXPECTED_STATES}, got {sorted(grouped)}")
    ids = [int(row["province_id"]) for row in province_rows]
    if len(ids) != len(set(ids)) or set(ids) != set(range(1, EXPECTED_PROVINCES + 1)):
        raise ValueError("Province IDs must be unique and cover 1–906 exactly")

    counts = {"MOS": 0, "VOR": 0, "OGO": 0}
    for state_id in range(1, EXPECTED_STATES + 1):
        row = districts.get(state_id, {})
        provinces = sorted(grouped[state_id], key=lambda p: int(p["province_id"]))
        owner = owner_for(state_id)
        counts[owner] += 1

        # Use the largest province's pixel coordinates as a stable victory point.
        largest = max(provinces, key=lambda p: int(p["area_pixels"]))
        vp_id = int(largest["province_id"])
        lon = float(row.get("centroid_lon_approx", "37.62"))
        lat = float(row.get("centroid_lat_approx", "55.75"))
        radius_km = math.hypot((lon - 37.62) * 53.5, (lat - 55.75) * 111)
        if state_id == 108:
            category, infrastructure, civs, arms, manpower = "rural", 2, 0, 0, 350_000
        else:
            category = (
                "large_city" if radius_km < 2.8 else
                "city" if radius_km < 5.5 else
                "large_town" if radius_km < 9 else "town"
            )
            infrastructure = 4 if radius_km < 3 else 3 if radius_km < 7 else 2
            civs = 2 if radius_km < 3.5 else 1 if state_id in INDUSTRIAL_STATES else 0
            arms = 1 if radius_km < 3.5 else int(
                state_id in INDUSTRIAL_STATES and state_id in VOR_STATES | OGO_STATES
            )
            manpower = max(65_000, min(160_000, 70_000 + len(provinces) * 3_500))

        ids_text = " ".join(p["province_id"] for p in provinces)
        lines = [
            "state = {",
            f" id = {state_id}",
            f' name = "STATE_{state_id}"',
            f" manpower = {manpower}",
            f" state_category = {category}",
            f" provinces = {{ {ids_text} }}",
            " history = {",
            f"  owner = {owner}",
            "  add_core_of = MOS",
        ]
        if owner != "MOS":
            lines.append(f"  add_core_of = {owner}")
        lines.extend([
            f"  victory_points = {{ {vp_id} {10 if radius_km < 3 else 5} }}",
            f"  buildings = {{ infrastructure = {infrastructure} industrial_complex = {civs} arms_factory = {arms} }}",
            " }",
            "}",
            "",
        ])
        (STATE_DIR / f"{state_id}-moscow.txt").write_text(
            "\n".join(lines), encoding="utf-8"
        )

    if counts != {"MOS": 82, "VOR": 14, "OGO": 12}:
        raise ValueError(f"Unexpected ownership distribution: {counts}")
    print(f"Wrote {EXPECTED_STATES} state files; {EXPECTED_PROVINCES} province IDs verified; ownership: {counts}")


if __name__ == "__main__":
    build()
