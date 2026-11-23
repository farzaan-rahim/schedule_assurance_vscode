# Schedule Assurance

VS Code-ready project assembled from the Python files supplied for the previous P6 planning application.

## What was preserved
All 13 supplied Python files are preserved byte-for-byte in `original_files/`. Reusable application code is also organized under `app/` and `scripts/`.

## Database decision
The old database implementation is intentionally not reused. The supplied `config.py` and `main.py` depended on the previous PostgreSQL/API structure, so exact copies are retained under `legacy_reference/` and `original_files/`. The active `app/main.py` and `app/config.py` are minimal database-independent starting points.

## Reused modules
- `app/importers/xer_parser.py`: XER table parser
- `app/importers/schedule_mapper.py`: raw XER to schedule-domain mapping
- `app/models/schedule.py`: Project/WBS/Activity/Relationship/Calendar/Schedule models
- `app/graph/schedule_graph.py`: adjacency indexes, traversal, cycles and topological sorting
- `app/health/models.py`: health-analysis models
- `app/health/rules.py`: supplied schedule quality rules
- `app/health/scoring.py`: supplied prototype health scoring
- `app/services/activity_resolution.py`: activity resolution result models
- `scripts/inspect_xer.py`, `scripts/list_xer_tables.py`: XER developer utilities

## Open in VS Code
1. Extract this ZIP.
2. Open the extracted folder in VS Code.
3. Create a virtual environment: `python -m venv .venv`
4. Activate it.
5. Install packages: `pip install -r requirements.txt`
6. Run the clean API shell: `uvicorn app.main:app --reload`
7. Open `http://127.0.0.1:8000/docs`.

## For VS Code AI Chat
Open the entire folder as the workspace. The AI assistant can then inspect `app/` for the organized code and `original_files/` when it needs the exact source snapshot.

## Next engineering target
Build a new persistence layer and baseline/current comparison engine without coupling them to the previous database.
