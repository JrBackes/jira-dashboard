from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services import sprint_metrics

router = APIRouter(prefix="/api/sprints", tags=["sprints"])


def _get_sprint_or_404(db: Session, sprint_id: int):
    sprint = sprint_metrics.get_sprint(db, sprint_id)
    if sprint is None:
        raise HTTPException(status_code=404, detail="Sprint não encontrada")
    return sprint


@router.get("")
def list_sprints(project: str | None = None, state: str | None = None, db: Session = Depends(get_db)):
    return sprint_metrics.list_sprints(db, project_key=project, state=state)


@router.get("/{sprint_id}/summary")
def sprint_summary(sprint_id: int, db: Session = Depends(get_db)):
    sprint = _get_sprint_or_404(db, sprint_id)
    return {"sprint": sprint, "status_counts": sprint_metrics.sprint_status_counts(db, sprint_id)}


@router.get("/{sprint_id}/scope-changes")
def sprint_scope_changes(sprint_id: int, db: Session = Depends(get_db)):
    sprint = _get_sprint_or_404(db, sprint_id)
    return sprint_metrics.sprint_scope_changes(db, sprint)


@router.get("/{sprint_id}/burndown")
def sprint_burndown(sprint_id: int, db: Session = Depends(get_db)):
    sprint = _get_sprint_or_404(db, sprint_id)
    return sprint_metrics.sprint_burndown(db, sprint)


@router.get("/{sprint_id}/velocity-history")
def sprint_velocity_history(sprint_id: int, limit: int = 6, db: Session = Depends(get_db)):
    sprint = _get_sprint_or_404(db, sprint_id)
    return sprint_metrics.velocity_history(db, sprint.board_id, limit=limit)


@router.get("/{sprint_id}/workload-by-status")
def sprint_workload_by_status(sprint_id: int, db: Session = Depends(get_db)):
    _get_sprint_or_404(db, sprint_id)
    return sprint_metrics.sprint_workload_by_status_and_person(db, sprint_id)
