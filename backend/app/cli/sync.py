"""CLI de sincronização com o Jira.

Uso:
    poetry run python -m app.cli.sync run --site TEC
    poetry run python -m app.cli.sync run --site CAP
    poetry run python -m app.cli.sync run --all
"""

import typer

from app.core.db import SessionLocal
from app.services.sync_service import PROJECT_KEY_BY_SITE, sync_site

app = typer.Typer()


@app.command()
def run(
    site: str = typer.Option(None, help="Chave do site (ex: TEC, CAP)"),
    all: bool = typer.Option(False, "--all", help="Sincroniza todos os sites configurados"),  # noqa: A002
) -> None:
    if not site and not all:
        typer.echo("Informe --site TEC|CAP ou --all")
        raise typer.Exit(code=1)

    site_keys = list(PROJECT_KEY_BY_SITE.keys()) if all else [site.upper()]

    for site_key in site_keys:
        typer.echo(f"Sincronizando site {site_key}...")
        db = SessionLocal()
        try:
            sync_run = sync_site(db, site_key)
            typer.echo(
                f"  -> {sync_run.status}, {sync_run.records_processed} registros processados"
            )
        finally:
            db.close()


if __name__ == "__main__":
    app()
