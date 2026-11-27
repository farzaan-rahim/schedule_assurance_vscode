# Schedule Assurance

Clean-room Primavera P6 schedule analysis with a NiceGUI planner workspace, FastAPI services and PostgreSQL persistence. Domain calculations remain independent of UI/database models. Imported P6 dates/float remain separate from calculated CPM values. See the [calculation](docs/phase6_calculation_contract.md), [persistence](docs/phase7_persistence_contract.md), [simulation/CPLI](docs/phase8_calculation_contract.md) and [UI](docs/phase9_ui_contract.md) contracts.

## Local startup (PowerShell)

Run all commands from the repository root. Python 3.11+ is required.

```powershell
cd C:\Github\schedule_assurance_vscode
# First setup only, if .venv does not exist:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If activation is unavailable, use `.\.venv\Scripts\python.exe` in place of `python` and `.\.venv\Scripts\alembic.exe` in place of `alembic`.

1. Configure a local `.env` at the repository root from `.env.example`. Copy it only if `.env` does not already exist; preserve existing credentials. Replace the development password placeholder and keep SA_DATABASE_URL consistent with the database role/port. `.env` is git-ignored; real credentials must not be committed.
2. Start PostgreSQL. With Docker Desktop running, the supplied Compose file creates the configured role/database on local port **5433**:

   ```powershell
   docker compose up -d postgres
   docker compose ps
   ```

   Alternatively use an existing native PostgreSQL installation. On this workstation PostgreSQL 18 is installed; the service can be inspected with `Get-Service -Name 'postgresql*'` and started with `Start-Service -Name postgresql-x64-18` when needed/authorized. Use an existing or explicitly created database and role; a running service alone does not create the application database. Native PostgreSQL commonly listens on **5432**. Example only:

   ```dotenv
   SA_DATABASE_URL=postgresql+psycopg://schedule_user:schedule_password@localhost:5432/schedule_assurance
   SA_STORAGE_ROOT=./var/source-files
   ```

3. Apply the existing Alembic migrations explicitly. Startup diagnostics do not create/upgrade tables:

   ```powershell
   alembic upgrade head
   alembic current
   ```

4. Start the application:

   ```powershell
   python -m uvicorn app.main:app --reload
   ```

5. Open the workspace: **http://127.0.0.1:8000/ui/**.
6. API documentation: **http://127.0.0.1:8000/docs**. OpenAPI JSON is `/openapi.json`; ReDoc is `/redoc`. These are parent FastAPI routes. The old `/ui/docs` URL redirects to `/docs`; no duplicate Swagger is mounted.

`pydantic-settings` loads `.env` from the repository root even if the process working directory differs. Environment variables take precedence. Source storage retains its existing working-directory-relative semantics, so run from the repository root or configure an absolute SA_STORAGE_ROOT. Restart after environment changes, or use **Recheck setup** for local `.env` changes; reload the page to discard old analysis context if switching databases.

## Runtime diagnostics and empty states

The startup log, `/api/runtime`, and UI distinguish:

| State | Meaning / action |
| --- | --- |
| UI available | The shell, navigation and setup instructions are available independently of PostgreSQL. |
| Setup required / UNCONFIGURED | No usable SA_DATABASE_URL was provided. Add it to repository `.env`. |
| INVALID_CONFIGURATION | The URL/settings could not be validated. Check configuration syntax. |
| DATABASE_UNAVAILABLE | Configured, but PostgreSQL could not be reached/authenticated. Check the service, role, database, host and port. |
| MIGRATIONS_REQUIRED | Reachable, but Alembic revisions differ from the application head. Run `alembic upgrade head`. |
| MIGRATIONS_UNKNOWN | Reachable, but migration inspection could not complete. Check permissions and `alembic current`. |
| READY | Database reachable; Alembic revision is current. Project/version controls can be enabled. |

Use `/api/runtime?refresh=true` for a fresh server check or **Recheck setup** in the workspace. Checks use short read-only diagnostic connections with connection/query timeouts. No URL/password/exception text is returned in diagnostics. `/api/health` remains a database-independent liveness endpoint.

Before database readiness, persistence-dependent actions are unavailable, but all menu destinations and `/setup` remain usable. No project, no version, no analysis run, NOT_EVALUATED/BLOCKED output, database setup and application-operation failure are distinct states. Long operations show an indeterminate spinner and actual operation label, not fabricated percentages.

## XER project preflight

Open **Schedule Versions** even when no application Project exists. Select an XER to inspect its P6 project code/name, source project ID, Data Date and activity/relationship/WBS counts. This scan reads metadata and counts only; it creates no project/version and stores no source file. The selected file is held in the active UI session until confirmed or replaced.

For a multi-project export, choose the source P6 project explicitly. The UI never picks the largest project automatically. A matching application Project shows **Project match confirmed**. A mismatch displays both codes and disables **Import confirmed XER**. Use **Choose matching project**, **Use existing project**, or **Create project from XER**. Creation prepopulates the detected code (read-only) and an editable project name, and reuses an existing exact-code project instead of duplicating it.

After project resolution, supply a version label/type and select **Import confirmed XER**. Only that action invokes parsing/mapping/persistence. The backend's exact project-code validation remains the final safeguard. The existing import API also accepts an optional `source_project_id` form field to select a particular P6 project from a multi-project file; original source bytes and hash identity are preserved.

## Repeatable planner UAT workflow

Use the versioned, explicitly synthetic comparison fixtures. They are not genuine P6 calibration data.

1. Open Schedule Versions and select `sample_data/sample_baseline.xer` for preflight. Choose **Create project from XER**, name `Planner UAT comparison`, or **Use existing project** when offered. The detected Project code is SYNTHETIC; no prior knowledge of it is required.
2. Confirm **Project match confirmed**, set label `UAT Baseline` and type BASELINE, then **Import confirmed XER**.
3. Select `sample_data/sample_current.xer` for preflight, confirm the same project match, set label `UAT Update` and type UPDATE, then import.
4. Activate UAT Update in Schedule Versions.
5. Open Schedule Health, verify the not-run state, then Analyze Health and inspect a rule.
6. Open DCMA, Run DCMA, expand metric notes/findings and CPT/CPLI availability reasons. Do not expect unsupported metrics to become PASS.
7. In Change Analysis select UAT Baseline as source and UAT Update as target. Run comparison. Check A1500 removed, A1700 added, A1200 renamed/delayed/duration increase/float deterioration, A1300 WBS movement and relationship type/lag changes. Try exact classification and WBS filters, sorting and pagination.
8. In Milestones select the same pair and View Milestones. Review movement, negative float and findings.
9. In CPM / Paths explicitly request milestone **M1400** by Activity ID/code; do not designate it contractual completion. The comparison fixtures intentionally lack usable calendar patterns and imported Late Finish, so calibration/scheduling may be blocked. Verify the reason is visible rather than changing fixture values to force a result.
10. For a supported positive CPM/path UAT, optionally export the **existing proprietary-free controlled fixture** to a temporary file:

    ```powershell
    python -c "from pathlib import Path; from tempfile import gettempdir; from tests.test_analysis_anchors import controlled_xer; p=Path(gettempdir())/'schedule_assurance_controlled_uat.xer'; p.write_bytes(controlled_xer()); print(p)"
    ```

    Create a separate Project code **P1**, name `Controlled CPM UAT`, import that clearly synthetic file as CURRENT, and explicitly select **F3** (internal ID 5) in CALIBRATION mode. Review timestamp provenance, six upstream activities, imported/calculated dates, availability, diagnostics and the connected controlling path. The unrelated UNRELATED activity must not join the path. Test INDEPENDENT without a finish (controlled error), then with `2026-01-05 14:00`. This fixture is not a replacement for NRG00800.xer or evidence of real-P6 equivalence.
11. Return to the SYNTHETIC project. In Reports choose UAT Baseline/UAT Update, leave the optional anchor unset, preview metadata, then download `Schedule Assurance Forensic Change Report.xlsx`. Unsupported resources/cost/definition comparisons remain Not evaluated with reasons. Reimporting identical bytes should produce the existing controlled duplicate-hash result.

### Browser UAT matrix

At **1366x768**, **1440x900**, and **1920x1080**, click all ten navigation items, collapse/reopen the sidebar, and inspect selectors/cards/long IDs/descriptions/WBS paths/dialogs. Exercise table pages of 50/100/200 rows, header sorting, exact filters, sticky headers, negative values and unavailable labels. Tab through named controls and verify focus visibility and textual status labels. Inspect actual loading during import/comparison/DCMA/CPM/Excel work. Record viewport measurements and screenshots only when actually inspected; server-side NiceGUI tests do not establish visual/browser conformance.

## Regression commands

```powershell
pytest -q -m "not external_xer and not postgres"
# An explicitly disposable database only:
$env:POSTGRES_TEST_DATABASE_URL='postgresql+psycopg://test_user:test_password@localhost:5432/disposable_test_database'
pytest -q -m postgres
```

The registered external_xer tests require the unavailable genuine `sample_data/NRG00800.xer`; it is not fabricated. Original source snapshots and legacy references are not activated or modified. No Ruff, authentication, Entra ID, tenancy, AI or Monte Carlo functionality is introduced by runtime/UAT hardening.
