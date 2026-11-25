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
        
        parsed_tables: dict [str, list[dict[str, Any]]] = {
            table_name: []
            for table_name in self.CORE_TABLES
        }

        current_table: str | None = None
        current_fields: list [str] = []

        with path.open (mode="r", encoding="utf-8", errors="replace",) as xer_file:
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
                        parsed_tables[current_table].append(row)

        return parsed_tables
