from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DATA_FOLDER = PROJECT_ROOT / "sample_data"

def find_xer_files() -> list[Path]:
    xer_files = list(SAMPLE_DATA_FOLDER.glob("*.xer"))
    if not xer_files:
        raise FileNotFoundError("No .xer files found in sample_data folder")
    return sorted(xer_files)

def list_tables (file_path: Path) -> list[str]:
    tables: list [str] = []

    with file_path.open (mode="r", encoding="utf-8", errors="replace",) as xer_file:
        for line in xer_file:
            line = line.rstrip ("\n\r")

            if line.startswith("%T\t"):
                parts = line.split("\t")

                if len(parts) >= 2:
                    tables.append(parts[1].strip())
    return tables

if __name__ == "__main__":
    xer_files = find_xer_files()

    for xer_file in xer_files:
        table_names = list_tables(xer_file)
        print(f"\nXER file: {xer_file.name}")
        print(f"Number of tables: {len(table_names)}\n")

        for index, table_name in enumerate(table_names, start=1):
            print(f"{index:>3}. {table_name}")