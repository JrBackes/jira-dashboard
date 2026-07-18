"""Endpoint para disparar e acompanhar o sync manual com o Jira a partir do frontend.

Roda em background (BackgroundTasks) porque um sync completo demora — a requisição
HTTP do botão "Atualizar agora" não pode ficar bloqueada esperando minutos.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.db import SessionLocal, get_db
from app.models import Site, SyncRun
from app.services.sync_service import PROJECT_KEY_BY_SITE, sync_site

router = APIRouter(prefix="/api/sync", tags=["sync"])

# Um "running" mais velho que isso é considerado travado (processo morreu sem atualizar o
# status) — não deve bloquear novos disparos para sempre.
_STALE_RUN_THRESHOLD = timedelta(minutes=20)


def _run_sync_in_background(site_keys: list[str]) -> None:
    for site_key in site_keys:
        db = SessionLocal()
        try:
            sync_site(db, site_key)
        except Exception:
            pass  # sync_site já registra o erro em sync_runs antes de propagar
        finally:
            db.close()


def _is_running(db: Session, site_id: int) -> bool:
    last_run = db.query(SyncRun).filter_by(site_id=site_id).order_by(SyncRun.started_at.desc()).first()
    if last_run is None or last_run.status != "running":
        return False
    return datetime.now(timezone.utc) - last_run.started_at.replace(tzinfo=timezone.utc) < _STALE_RUN_THRESHOLD


@router.get("/status")
def sync_status(db: Session = Depends(get_db)) -> list[dict]:
    result = []
    for site_key in PROJECT_KEY_BY_SITE:
        site = db.query(Site).filter_by(key=site_key).one_or_none()
        if site is None:
            result.append({"site": site_key, "last_run": None})
            continue
        last_run = db.query(SyncRun).filter_by(site_id=site.id).order_by(SyncRun.started_at.desc()).first()
        result.append(
            {
                "site": site_key,
                "last_run": last_run
                and {
                    "status": last_run.status,
                    "started_at": last_run.started_at,
                    "finished_at": last_run.finished_at,
                    "records_processed": last_run.records_processed,
                    "error_message": last_run.error_message,
                },
            }
        )
    return result


@router.post("/trigger")
def trigger_sync(background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> dict:
    site_keys = list(PROJECT_KEY_BY_SITE.keys())
    already_running = []
    to_trigger = []
    for site_key in site_keys:
        site = db.query(Site).filter_by(key=site_key).one_or_none()
        if site is not None and _is_running(db, site.id):
            already_running.append(site_key)
        else:
            to_trigger.append(site_key)

    if to_trigger:
        background_tasks.add_task(_run_sync_in_background, to_trigger)

    return {"triggered": to_trigger, "already_running": already_running}
