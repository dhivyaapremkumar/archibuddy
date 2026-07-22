"""
Compliance rules engine for TN Compliance Copilot.

RULES below is the single source of truth for setback / FSI / parking
figures. It is sourced from secondary TNCDBR 2019 summaries, NOT the
official gazette text, and must be verified against the primary source
(and any amendments since) before this is used for anything a client
or authority will see. Everything downstream (API, DXF export, PDF
report) reads from this dict, so updating it here is the only change
needed once verified figures are available.

All linear values are in metres (TNCDBR's native unit). Plot dimensions
are accepted from users in feet (the common convention in TN real
estate) and converted internally.
"""

FT_PER_M = 3.28084
SQFT_PER_SQM = 10.7639

RULES = {
    "version": "TNCDBR-2019-draft (unverified secondary source)",
    "fsi": 2.0,
    "front_setback_by_road_width": [
        {"max_road_width": 9, "setback": 1.5},
        {"max_road_width": 18, "setback": 3.0},
        {"max_road_width": 30.5, "setback": 4.5},
        {"max_road_width": float("inf"), "setback": 6.0},
    ],
    "rear_setback_by_height": [
        {"max_height": 7, "setback": 1.5},
        {"max_height": 12, "setback": 1.5},
        # beyond the encoded source range for non-high-rise — needs verification
        {"max_height": float("inf"), "setback": 2.5},
    ],
    # Two-dimensional table: pick the height band first, then the
    # plot-width row within that band. "sides": "one" = setback required
    # on one side only (the envelope preview applies it symmetrically).
    "side_setback_bands": [
        {
            "max_height": 7,
            "widths": [
                {"max_plot_width": 9, "setback": 1.0, "sides": "one"},
                {"max_plot_width": float("inf"), "setback": 1.0, "sides": "both"},
            ],
        },
        {
            "max_height": 12,
            "widths": [
                {"max_plot_width": 6, "setback": 1.0, "sides": "one"},
                {"max_plot_width": 9, "setback": 1.5, "sides": "one"},
                {"max_plot_width": float("inf"), "setback": 1.5, "sides": "both"},
            ],
        },
    ],
    # Approximate storey height per floor option — verify against actual
    # sanctioned storey heights before relying on this for height-band lookups.
    "floor_height_m": {"Ground only": 3.5, "G + 1": 6.5, "G + 2": 9.5},
    "dwelling_units": {"Ground only": 1, "G + 1": 2, "G + 2": 3},
    # Placeholder — TNCDBR Annexure-IV parking norms are more nuanced
    # (vary by unit count/size and use) and are not yet encoded.
    "parking_per_unit": 1,
}


def ft_to_m(ft: float) -> float:
    return ft / FT_PER_M


def m_to_ft(m: float) -> float:
    return m * FT_PER_M


def _lookup(table, key, field):
    for row in table:
        if key <= row[field]:
            return row
    return table[-1]


def lookup_side_setback(height_m: float, plot_width_m: float) -> dict:
    band = _lookup(RULES["side_setback_bands"], height_m, "max_height")
    return _lookup(band["widths"], plot_width_m, "max_plot_width")


def compute_compliance(frontage_ft: float, depth_ft: float, road_ft: float, floors: str) -> dict:
    if floors not in RULES["floor_height_m"]:
        raise ValueError(f"Unknown floors option: {floors!r}")

    frontage_m = ft_to_m(frontage_ft)
    depth_m = ft_to_m(depth_ft)
    road_m = ft_to_m(road_ft)
    height_m = RULES["floor_height_m"][floors]

    front = _lookup(RULES["front_setback_by_road_width"], road_m, "max_road_width")["setback"]
    rear = _lookup(RULES["rear_setback_by_height"], height_m, "max_height")["setback"]
    side_row = lookup_side_setback(height_m, frontage_m)
    side = side_row["setback"]

    buildable_width_m = max(frontage_m - 2 * side, 0)
    buildable_depth_m = max(depth_m - front - rear, 0)
    buildable_area_sqm = buildable_width_m * buildable_depth_m
    plot_area_sqm = frontage_m * depth_m
    max_fsi_area_sqm = plot_area_sqm * RULES["fsi"]

    units = RULES["dwelling_units"].get(floors, 1)
    parking = units * RULES["parking_per_unit"]

    warning = None
    if buildable_width_m <= 0 or buildable_depth_m <= 0:
        warning = (
            "Plot is too narrow or too shallow for the required setbacks "
            "at this height — no buildable area remains."
        )

    return {
        "inputs": {
            "frontage_ft": frontage_ft,
            "depth_ft": depth_ft,
            "road_ft": road_ft,
            "floors": floors,
        },
        "frontage_m": frontage_m,
        "depth_m": depth_m,
        "front_m": front,
        "side_m": side,
        "rear_m": rear,
        "front_ft": m_to_ft(front),
        "side_ft": m_to_ft(side),
        "rear_ft": m_to_ft(rear),
        "side_applies_to": side_row["sides"],
        "buildable_width_m": buildable_width_m,
        "buildable_depth_m": buildable_depth_m,
        "plot_sqft": plot_area_sqm * SQFT_PER_SQM,
        "max_fsi_sqft": max_fsi_area_sqm * SQFT_PER_SQM,
        "buildable_sqft": buildable_area_sqm * SQFT_PER_SQM,
        "parking": parking,
        "warning": warning,
        "rules_version": RULES["version"],
    }
