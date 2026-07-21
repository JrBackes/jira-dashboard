from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.services import tech_map_service

router = APIRouter(prefix="/api/tech-map", tags=["tech-map"])


class TechMapImportRequest(BaseModel):
    tsv: str
    sheet_name: str | None = None


@router.post("/import")
def import_tech_map(payload: TechMapImportRequest, db: Session = Depends(get_db)) -> dict:
    """Importa o Mapa de Tecnologia a partir de texto colado (TSV) — sem credencial do Google,
    ver `tech_map_service.import_tech_map_from_tsv`."""
    sheet_name = payload.sheet_name or get_settings().tech_map_sheet_name
    try:
        count = tech_map_service.import_tech_map_from_tsv(db, sheet_name, payload.tsv)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"entries_imported": count}


@router.get("/sprints/{sprint_id}")
def tech_map_for_sprint(sprint_id: int, db: Session = Depends(get_db)) -> list[dict]:
    return tech_map_service.get_tech_map_for_sprint(db, sprint_id)
