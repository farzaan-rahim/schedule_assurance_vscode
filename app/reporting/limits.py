from dataclasses import dataclass


@dataclass(frozen=True)
class ReportLimits:
    # Explicit resource guard, never a silent detail truncation.
    maximum_rows_per_section: int = 200_000
    maximum_upload_bytes: int = 100 * 1024 * 1024

    def __post_init__(self):
        if not 1 <= self.maximum_rows_per_section <= 1_048_570:
            raise ValueError("Report row limit must fit an Excel worksheet.")
        if self.maximum_upload_bytes < 1:
            raise ValueError("Upload limit must be positive.")


class ReportLimitError(ValueError):
    pass
