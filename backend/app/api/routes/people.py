from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services import person_metrics

router = APIRouter(prefix="/api/people", tags=["people"])


@router.get("")
def list_people(project: str | None = None, db: Session = Depends(get_db)):
    return person_metrics.list_people(db, project_key=project)


@router.get("/{person_id}/workload")
def person_workload(
    person_id: int, project: str | None = None, sprint_id: int | None = None, db: Session = Depends(get_db)
):
    if person_metrics.get_person(db, person_id) is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return person_metrics.person_workload(db, person_id, project_key=project, sprint_id=sprint_id)


@router.get("/{person_id}/highlights")
def person_highlights(person_id: int, sprint_id: int | None = None, db: Session = Depends(get_db)):
    if person_metrics.get_person(db, person_id) is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return person_metrics.person_highlights(db, person_id, sprint_id=sprint_id)


@router.get("/ranking/weekly")
def weekly_time_ranking(project: str | None = None, sprint_id: int | None = None, db: Session = Depends(get_db)):
    return person_metrics.weekly_time_ranking(db, project_key=project, sprint_id=sprint_id)


@router.get("/ranking/daily")
def daily_time_breakdown(project: str | None = None, sprint_id: int | None = None, db: Session = Depends(get_db)):
    return person_metrics.daily_time_breakdown(db, project_key=project, sprint_id=sprint_id)
