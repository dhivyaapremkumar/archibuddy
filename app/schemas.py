"""
DXF export for the buildable envelope, using ezdxf.

Units: metres. Origin at the plot's front-left corner; +y runs from the
road-facing edge toward the rear. Two closed polylines on separate
layers: PLOT_BOUNDARY (the full plot) and BUILDABLE_ENVELOPE (the
compliant buildable area after setbacks).
"""
import io
import tempfile

import ezdxf


def build_dxf_bytes(check_result: dict) -> bytes:
    frontage_m = check_result["frontage_m"]
    depth_m = check_result["depth_m"]
    side_m = check_result["side_m"]
    front_m = check_result["front_m"]
    rear_m = check_result["rear_m"]

    doc = ezdxf.new("R2010")
    doc.layers.add("PLOT_BOUNDARY", color=7)
    doc.layers.add("BUILDABLE_ENVELOPE", color=5)
    msp = doc.modelspace()

    plot_pts = [(0, 0), (frontage_m, 0), (frontage_m, depth_m), (0, depth_m), (0, 0)]
    msp.add_lwpolyline(plot_pts, dxfattribs={"layer": "PLOT_BOUNDARY"})

    bx0, bx1 = side_m, frontage_m - side_m
    by0, by1 = front_m, depth_m - rear_m
    build_pts = [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1), (bx0, by0)]
    msp.add_lwpolyline(build_pts, dxfattribs={"layer": "BUILDABLE_ENVELOPE"})

    # ezdxf writes to a path or a text stream; use a temp file for a clean
    # round trip to bytes rather than relying on text-stream encoding quirks.
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        doc.saveas(tmp_path)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        import os
        os.unlink(tmp_path)
