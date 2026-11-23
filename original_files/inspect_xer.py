from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_DATA_FOLDER = PROJECT_ROOT / "sample_data"

def find_xer_files() -> list [Path]:
    return list (SAMPLE_DATA_FOLDER.glob("*.xer"))

def inspect_xer (file_path : Path, lines_to_show: int = 30) -> None:
    print (f"\nFile Found: {file_path.name}")
    print (f"\nFile Size: {file_path.stat().st_size /1024/1024:.2f} MB")
    print ("\nFirst lines:\n")

    with file_path.open (mode="r", encoding="utf-8", errors="replace",) as xer_file:
        for line_number, line in enumerate (xer_file, start=1):
            print (f"{line_number}: {line.rstrip()}")

            if line_number >= lines_to_show:
                break

if __name__=="__main__":
    xer_files= find_xer_files()

    if not xer_files:
        print("No .xer files found in sample_data folder")

    else:
        print(f"Found {len(xer_files)} .XER files")

        for xer_file in xer_files:
            inspect_xer(xer_file)