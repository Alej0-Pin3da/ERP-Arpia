"""Persist WARN/ERROR migration entries into Migracion_Omisiones (MIG-1/MIG-2).

The CLI calls this in commit mode only, right after the JSON trace is
written (design D7): every WARN/ERROR entry of the run becomes a row with
``corrida_id`` = the trace file stem, so re-runs always create new corridas
(full history, no upsert). Any DB failure raises — the caller wraps the
call in try/except and emits a WARN, so the run itself is never aborted
(MIG-2) and the already-written JSON trace is never touched.
"""

from __future__ import annotations

from app.models.migracion import MigracionOmision
from migrate.report import LEVEL_ERROR, LEVEL_WARN, Report


def persistir_omisiones(db, run_report: Report, corrida_id: str) -> int:
    """Insert one ``MigracionOmision`` per WARN/ERROR entry of the run.

    INFO entries are skipped; ``fase`` is the run-level fase label
    (``report.fase`` — e.g. "F5" for a single-phase run, "F0+F1" for
    multi-phase runs). Returns the number of rows inserted.
    """
    filas = [
        MigracionOmision(
            corrida_id=corrida_id,
            fase=run_report.fase,
            hoja=entry.hoja,
            fila=entry.fila,
            celda=entry.celda,
            nivel=entry.nivel,
            mensaje=entry.mensaje,
        )
        for entry in run_report.entradas
        if entry.nivel in (LEVEL_WARN, LEVEL_ERROR)
    ]
    db.add_all(filas)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return len(filas)
