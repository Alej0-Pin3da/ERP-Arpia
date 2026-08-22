"""Migration report: level-based (INFO/WARN/ERROR) with sheet/row/cell detail.

Every phase produces one report. A report is rendered to stdout and persisted
as JSON under ``reports/`` (gitignored). ERROR entries are the ones F7 uses to
decide a non-zero exit code; WARN entries record divergences with a cause.

Traceability (spec EXM-6): the CLI persists a run-level report per execution
(``reports/migracion_YYYYMMDD_HHMMSS.json``) that records the executed phases,
counts per phase, all INFO/ERROR/WARN entries, a timestamp and a content hash.
The hash is computed over the stable run content (phases, counts, entries) so
re-running the same source+phases yields the same hash and a changed workbook
produces a different one (drift / re-run detection).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

DEFAULT_REPORTS_DIR = Path(__file__).resolve().parent / "reports"

# Severity levels, ascending. INFO is informative, WARN marks a divergence that
# does not block, ERROR marks a broken check / failed row that must block.
LEVEL_INFO = "INFO"
LEVEL_WARN = "WARN"
LEVEL_ERROR = "ERROR"

NIVELES = (LEVEL_INFO, LEVEL_WARN, LEVEL_ERROR)


@dataclass
class ReportEntry:
    nivel: str
    hoja: str
    fila: int | None
    celda: str | None
    mensaje: str


@dataclass
class Report:
    fase: str
    modo: str
    generado: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    entradas: list[ReportEntry] = field(default_factory=list)
    fases: list[str] = field(default_factory=list)  # EXM-6: phases of the run
    conteos_por_fase: dict[str, dict[str, int]] = field(default_factory=dict)  # EXM-6
    hash_contenido: str | None = None  # EXM-6: content hash (drift detection)

    def info(self, hoja: str, fila: int | None, celda: str | None, mensaje: str) -> None:
        self._add(LEVEL_INFO, hoja, fila, celda, mensaje)

    def warn(self, hoja: str, fila: int | None, celda: str | None, mensaje: str) -> None:
        self._add(LEVEL_WARN, hoja, fila, celda, mensaje)

    def error(self, hoja: str, fila: int | None, celda: str | None, mensaje: str) -> None:
        self._add(LEVEL_ERROR, hoja, fila, celda, mensaje)

    def _add(
        self, nivel: str, hoja: str, fila: int | None, celda: str | None, mensaje: str
    ) -> None:
        self.entradas.append(
            ReportEntry(nivel=nivel, hoja=hoja, fila=fila, celda=celda, mensaje=mensaje)
        )

    def count(self, nivel: str) -> int:
        return sum(1 for entry in self.entradas if entry.nivel == nivel)

    @property
    def tiene_errores(self) -> bool:
        return self.count(LEVEL_ERROR) > 0

    tenga_errores = tiene_errores  # alias (contract tests use the subjunctive form)

    def resumen_lineas(self) -> list[str]:
        """Compact stdout summary: one line per entry, plus totals."""
        lines = [f"--- Reporte migracion [{self.modo}] fase {self.fase} ---"]
        for entry in self.entradas:
            loc = entry.hoja
            if entry.fila is not None:
                loc = f"{loc} - fila {entry.fila}"
            if entry.celda:
                loc = f"{loc} (celda {entry.celda})"
            lines.append(f"[{entry.nivel}] {loc}: {entry.mensaje}")
        lines.append(
            f"Totales: {self.count(LEVEL_ERROR)} ERROR, "
            f"{self.count(LEVEL_WARN)} WARN, {self.count(LEVEL_INFO)} INFO"
        )
        return lines

    def dump(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)

    def calcular_hash(self) -> str:
        """SHA256 of the stable run content (EXM-6 drift detection).

        The timestamp (``generado``) and the hash field itself are excluded so
        re-running the same source+phases produces the same hash; a changed
        workbook (different entries/counts) produces a different one.
        """
        payload = asdict(self)
        payload.pop("generado", None)
        payload.pop("hash_contenido", None)
        canon = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(canon.encode("utf-8")).hexdigest()

    def write(self, reports_dir: Path | str | None = None) -> Path:
        """Persist the JSON report (gitignored) under reports/, returning the path."""
        target_dir = Path(reports_dir) if reports_dir else DEFAULT_REPORTS_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = target_dir / f"migracion_{stamp}.json"
        self.hash_contenido = self.calcular_hash()
        path.write_text(self.dump(), encoding="utf-8")
        return path
