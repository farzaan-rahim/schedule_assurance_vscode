from pathlib import Path
from typing import Any

class XERParser:
    CORE_TABLES = {
        "PROJECT",
        "SCHEDOPTIONS",
        "PROJWBS",
        "TASK",
        "TASKPRED",
        "CALENDAR",
        "RSRC",
        "TASKRSRC",
        "ACTVTYPE",
        "ACTVCODE",
        "TASKACTV",
        "UDFTYPE",
        "UDFVALUE",
    }

    def parse(self, file_path: str | Path) -> dict[str, list[dict[str, Any]]]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Xer file not found at {path}")
        with path.open(mode="r", encoding="utf-8", errors="replace") as stream:
            return self.parse_stream(stream)

    def parse_stream(self, stream):
        tables = {name: [] for name in self.CORE_TABLES}
        for table, row in self.iter_rows(stream):
            tables[table].append(row)
        return tables

    def iter_rows(self, xer_file):
        """Stream supported table rows without retaining a full schedule."""
        current_table = None
        current_fields = []
        for raw_line in xer_file:
            line = raw_line.rstrip("\r\n")

            if not line:
                continue

            parts = line.split("\t")
            record_type = parts[0]

            if record_type == "%T":
                current_table = (
                    parts[1].strip()
                    if len(parts) > 1
                    else None)
                current_fields = []

            elif record_type == "%F":
                if current_table in self.CORE_TABLES:
                    current_fields = parts[1:]

            elif record_type == "%R":
                if (
                    current_table in self.CORE_TABLES
                    and current_fields
                ):
                    values = parts[1:]

                    if len(values) < len(current_fields):
                        values.extend(
                            [""] * (
                                len(current_fields) - len(values)
                                )
                        )
                    if len(values) > len(current_fields):
                        values = values[:len(current_fields)]

                    row = dict(zip(current_fields, values))
                    yield current_table, row
