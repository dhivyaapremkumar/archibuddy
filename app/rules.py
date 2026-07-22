from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.features.compliance import models
from app.features.compliance.dxf_export import build_dxf_bytes
from app.features.compliance.pdf_export import build_pdf_bytes
from app.features.compliance.rules import compute_compliance
from app.features.compliance.schemas import ComplianceCheckRequest, ComplianceCheckResponse

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


def _record_to_result_dict(record: models.ComplianceCheck) -> dict:
    """Reconstruct the shape compute_compliance() returns, from a saved row,
    so the export functions can work directly off history entries."""
    frontage_m = record.frontage_ft / 3.28084
    depth_m = record.depth_ft / 3.28084
    return {
        "inputs": {
            "frontage_ft": record.frontage_ft,
            "depth_ft": record.depth_ft,
            "road_ft": record.road_ft,
            "floors": record.floors,
        },
        "frontage_m": frontage_m,
        "depth_m": depth_m,
        "front_m": record.front_m,
        "side_m": record.side_m,
        "rear_m": record.rear_m,
        "front_ft": record.front_m * 3.28084,
        "side_ft": record.side_m * 3.28084,
        "rear_ft": record.rear_m * 3.28084,
        "plot_sqft": record.plot_sqft,
        "max_fsi_sqft": record.max_fsi_sqft,
        "buildable_sqft": record.buildable_sqft,
        "parking": record.parking,
        "warning": record.warning,
        "rules_version": record.rules_version,
    }


@router.post("/check", response_model=ComplianceCheckResponse)
def check_compliance(payload: ComplianceCheckRequest, db: Session = Depends(get_db)):
    result = compute_compliance(payload.frontage_ft, payload.depth_ft, payload.road_ft, payload.floors)

    record = models.ComplianceCheck(
        frontage_ft=payload.frontage_ft,
        depth_ft=payload.depth_ft,
        road_ft=payload.road_ft,
        floors=payload.floors,
        front_m=result["front_m"],
        side_m=result["side_m"],
        rear_m=result["rear_m"],
        plot_sqft=result["plot_sqft"],
        max_fsi_sqft=result["max_fsi_sqft"],
        buildable_sqft=result["buildable_sqft"],
        parking=result["parking"],
        warning=result["warning"],
        rules_version=result["rules_version"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ComplianceCheckResponse(
        id=record.id,
        created_at=record.created_at.isoformat(),
        frontage_ft=record.frontage_ft,
        depth_ft=record.depth_ft,
        road_ft=record.road_ft,
        floors=record.floors,
        front_ft=result["front_ft"],
        side_ft=result["side_ft"],
        rear_ft=result["rear_ft"],
        side_applies_to=result["side_applies_to"],
        plot_sqft=result["plot_sqft"],
        max_fsi_sqft=result["max_fsi_sqft"],
        buildable_sqft=result["buildable_sqft"],
        parking=result["parking"],
        warning=result["warning"],
        rules_version=result["rules_version"],
    )


@router.get("/history")
def list_history(db: Session = Depends(get_db), limit: int = 20):
    records = (
        db.query(models.ComplianceCheck)
        .order_by(models.ComplianceCheck.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "frontage_ft": r.frontage_ft,
            "depth_ft": r.depth_ft,
            "road_ft": r.road_ft,
            "floors": r.floors,
            "max_fsi_sqft": r.max_fsi_sqft,
            "warning": r.warning,
        }
        for r in records
    ]


def _get_record_or_404(check_id: int, db: Session) -> models.ComplianceCheck:
    record = db.query(models.ComplianceCheck).filter(models.ComplianceCheck.id == check_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Compliance check not found")
    return record


@router.get("/{check_id}", response_model=ComplianceCheckResponse)
def get_check(check_id: int, db: Session = Depends(get_db)):
    record = _get_record_or_404(check_id, db)
    result = _record_to_result_dict(record)
    return ComplianceCheckResponse(
        id=record.id,
        created_at=record.created_at.isoformat(),
        frontage_ft=record.frontage_ft,
        depth_ft=record.depth_ft,
        road_ft=record.road_ft,
        floors=record.floors,
        front_ft=result["front_ft"],
        side_ft=result["side_ft"],
        rear_ft=result["rear_ft"],
        side_applies_to="",
        plot_sqft=result["plot_sqft"],
        max_fsi_sqft=result["max_fsi_sqft"],
        buildable_sqft=result["buildable_sqft"],
        parking=result["parking"],
        warning=result["warning"],
        rules_version=result["rules_version"],
    )


@router.get("/{check_id}/export/dxf")
def export_dxf(check_id: int, db: Session = Depends(get_db)):
    record = _get_record_or_404(check_id, db)
    result = _record_to_result_dict(record)
    dxf_bytes = build_dxf_bytes(result)
    return Response(
        content=dxf_bytes,
        media_type="application/dxf",
        headers={"Content-Disposition": f'attachment; filename="buildable_envelope_{check_id}.dxf"'},
    )


@router.get("/{check_id}/export/pdf")
def export_pdf(check_id: int, db: Session = Depends(get_db)):
    record = _get_record_or_404(check_id, db)
    result = _record_to_result_dict(record)
    pdf_bytes = build_pdf_bytes(result)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="compliance_report_{check_id}.pdf"'},
    )
