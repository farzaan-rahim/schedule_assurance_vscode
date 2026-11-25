# Phase 7: imported-schedule persistence contract

## Scope and validation

Phase 7 adds PostgreSQL persistence around the existing canonical domain. It does not change schedule calculations or persist analytical results. Completion authority, Analysis Anchor selection, progress support, imported/calculated separation, and all earlier calculation contracts remain intact. DCMA Critical Path Test and CPLI remain **NOT_EVALUATED**.

Initial local regression, before implementation:

```text
pytest -q -m "not external_xer"
556 passed, 2 deselected, 1 warning in 27.31s
```

Final independently run suites:

```text
pytest -q -m "not external_xer and not postgres"
582 passed, 38 deselected, 1 warning in 25.91s

pytest -q -m postgres
36 passed, 584 deselected, 1 warning in 27.24s
```

The PostgreSQL run used a task-owned, isolated native **PostgreSQL 18.4** cluster on loopback port 55437, with an explicitly disposable database. Each test used a separately generated schema and applied Alembic migrations. No SQLite test is represented as PostgreSQL validation. All generated test schemas were removed. The existing system PostgreSQL service was not changed. The temporary cluster was stopped after validation.

The Docker CLI was available but its daemon was unavailable. The supplied Compose configuration passed `docker compose config --quiet`; its PostgreSQL 17 container was not started or integration-tested. Native PostgreSQL provided actual UUID, JSONB, FK, uniqueness, index, trigger, migration, and transaction validation.

All 88 snapshotted domain/analytical/import/reporting Python files and existing methodology documents were byte-for-byte unchanged. The sole existing application integration change is registering a new route module in `app/main.py`.

## Dependencies and configuration

Requirements add SQLAlchemy 2.x, Alembic >=1.16,<2, and psycopg 3 (`psycopg[binary]`). Existing pydantic-settings is reused. No Supabase SDK, storage, authentication, realtime, or function dependency is added.

`PersistenceSettings` reads `SA_` environment variables or a local `.env`:

| Variable | Meaning |
| --- | --- |
| SA_DATABASE_URL | Secret PostgreSQL/psycopg connection URL; optional until a persistence operation is requested |
| SA_STORAGE_ROOT | Service-owned source-file directory; defaults to `./var/source-files`, relative to process working directory |
| SA_MAXIMUM_UPLOAD_BYTES | Positive upload limit; defaults to 104857600 bytes |

`.env.example` contains development placeholders. Supply your own password, URL-encode URL credentials when necessary, and keep real `.env` files out of version control. Docker Compose independently consumes `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, and `POSTGRES_PORT` (default local port 5433).

Typical local setup from the repository root:

```powershell
python -m pip install -r requirements.txt
# Copy .env.example to .env and set local credentials.
docker compose up -d postgres
alembic upgrade head
uvicorn app.main:app --reload
```

An existing standard PostgreSQL server can be used instead of Docker. Alembic is the production schema mechanism; there is no `create_all()` startup path. Without a configured database, existing upload-based analytical routes continue working and persistence routes return a controlled 503. Engines are created lazily. Psycopg prepared statements are disabled for compatibility with external connection poolers; deployment-specific TLS/pool settings remain operator configuration.

## Domain boundary

```text
source bytes -> existing ScheduleImportService -> canonical Schedule
                                              -> mapper -> repositories -> PostgreSQL
PostgreSQL -> repositories -> mapper -> canonical Schedule -> unchanged analytical services
```

`Schedule`, `Activity`, `Relationship`, WBS/resource/code/UDF dataclasses, ComparisonResult, CPMResult, and ForensicChangeReport remain domain types. ORM classes exist only in `app/persistence/models`. Repositories return ORM objects only within persistence; services expose frozen project/version DTOs or canonical schedules. Route handlers orchestrate services and contain no SQL. No analytical service accepts an ORM object.

Typed mapper field maps distinguish source IDs from database UUID foreign keys. Optional indexes on a reloaded Schedule are rebuilt using existing domain helpers. Source ordering is retained, including merged resolved/unresolved relationship ordering. Original source project identity/name/dates are snapshotted on each version; subsequently renaming a catalogue Project does not change an imported Schedule.

## Schema (17 imported-data tables)

| Table | Purpose |
| --- | --- |
| projects | UUID identity; unique project code, name, description, active state, UTC created/updated metadata |
| schedule_versions | UUID and project FK; label/type/source SHA and P6 identity; Data Date, source project dates, import state/time and six population counts |
| source_files | One/version; original/generated names, media type, byte size, SHA-256, relative storage path and UTC creation time |
| wbs | Source identity/parent, code/name, stable code path and same-version parent FK |
| calendars | Source identity/type/base link; raw clndr_data, hours metadata, parsed work periods/exceptions/diagnostics as JSONB |
| activities | Every current canonical Activity field, plus same-version WBS/calendar FKs and source identity |
| relationships | Resolved predecessor/successor activity FKs, source identity, canonical/raw type and signed lag hours |
| unresolved_relationships | Original endpoint IDs and known nullable endpoint FKs, without inventing missing/external activities |
| resources | Per-version source identity/code/name, hierarchy, calendar/type/active fields and raw imported resource fields |
| resource_assignments | TASKRSRC identity, source and UUID links, currently imported quantities, costs, dates and raw fields |
| activity_code_types | Scope/project/WBS metadata and source type identity |
| activity_code_values | Values, source/type identities and hierarchical parent links |
| activity_code_assignments | Source associations and same-version activity/type/value links |
| udf_definitions | Subject/table, field identity, labels and source metadata |
| udf_values | Original subject/foreign object, typed and raw values; TASK-only activity link |
| scheduling_options | Phase 6D typed P6 scheduling options plus ordered raw source field/value pairs in JSONB |
| import_diagnostics | Severity/code/message/table/field, related source ID when available, lossless raw value and metadata JSONB |

UUIDs are generated in the application and stored as PostgreSQL UUIDs. Hierarchical/associated data use same-version composite foreign keys, deferred for insertion order. Source identity remains separate from UUID identity. `Calendar.project_id` and Activity Code scope `project_id` fields retain their original P6 string meaning; database Project identity is reached through ScheduleVersion.

Activities are unique on `(schedule_version_id, source_task_id)`. Visible Activity IDs/codes are deliberately **not unique**; `(schedule_version_id, activity_code)` has a non-unique search index. Source relationship IDs are not forced unique where the canonical importer can preserve duplicate source records.

Imported P6 scheduling timestamps use project-local, timezone-naive PostgreSQL timestamps; timezone-aware imported scheduling values are rejected rather than silently converted. Audit timestamps use timezone-aware UTC. Numeric durations, floats, quantities and costs retain the current domain's binary floating-point representation using DOUBLE PRECISION; persistence adds no rounding, currency interpretation or cost aggregation.

JSONB is used for hierarchical calendar data, raw source dictionaries/options and diagnostic metadata, rather than hiding normal activity fields in a giant document. Calendar round trips preserve the concrete calendar class, split/overnight periods, exceptions, fractional timestamps and diagnostics. A closed tagged diagnostic codec preserves supported Python scalar/container/date/time types without pickle or dynamic loading. Non-TASK UDFs never acquire an activity FK merely because their foreign ID matches a task ID.

## Project/version and immutability policies

A Project is identified by an independent UUID, with a unique project code for controlled automatic source resolution. An explicit project UUID must match the imported P6 project code. The importer does not silently rename an existing catalogue project.

Version types are BASELINE, UPDATE, CURRENT and SNAPSHOT. Multiple baselines and multiple CURRENT-labelled versions are allowed; the latter is a classification, not an implicit mutable current-version pointer. Filename is not identity. Within one Project the same SHA-256 is rejected, even with another label, filename or type. A new version UUID is returned for a distinct successful import. Concurrent identical imports have exactly one committed winner and one controlled duplicate response.

A successful ScheduleVersion and **all** imported child data are immutable. PostgreSQL triggers enforce this for INSERT/UPDATE/DELETE and prevent destructive TRUNCATE when successful imports exist. A child write locks its version row so it cannot race sealing. A version starts IMPORTING; sealing requires matching source hash metadata and exact activity/relationship/WBS/calendar/resource/assignment counts. The normal service commits only SUCCEEDED versions. Import success means the existing importer produced a canonical Schedule; it does not claim that CPM or any other analysis is fully calculable. Existing analytical diagnostics and directional availability still determine that. FAILED is reserved schema vocabulary; failed service imports roll back their rows rather than publishing partial versions. Project catalogue fields remain independently editable through repository-level operations; no edit/delete/version mutation API is introduced.

Migration/owner privileges can intentionally change schema or disable guards. Deploy with a separate migration role and an application role without schema/trigger-management privileges. This is database immutability enforcement under ordinary DML permissions, not protection from a database administrator.

## Storage and transaction contract

1. Validate a plain filename, `.xer` extension, nonempty content and configured size limit.
2. Compute exact-byte SHA-256.
3. Generate `<version-uuid>/<source-uuid-hex>.xer` beneath the configured storage root, exclusively create it, flush and fsync.
4. Invoke the existing importer without changing its normalization or analytical validation.
5. Resolve/create Project; reject project mismatch or duplicate hash.
6. Create IMPORTING version/source metadata; insert canonical imported data in batches; persist import diagnostics.
7. Seal the complete version, then commit once.

Storage metadata never stores an absolute workstation path or source BLOB. Filenames containing traversal, directories, drive separators or control characters are rejected. Resolved paths must stay beneath the root, including symlink/junction resolution. Cleanup verifies generated filename/version ownership and only removes the exact orphan file and its empty directory. The storage root must be service-owned; it is not an arbitrary shared writable directory.

Known failures roll back the entire database transaction, including a newly auto-created project, and remove the task-owned orphan source. The unique database hash constraint handles concurrent races. A database transaction and a filesystem write are not a distributed atomic transaction: if commit acknowledgement fails, the service checks for its source row with a fresh connection. A referenced file is retained and a controlled `commit_outcome_unknown` result includes the version UUID. If that check is unavailable, the file is also retained for reconciliation; if absence is proven, cleanup proceeds. Tests cover failures before commit and after a real server commit. No background reconciliation or filesystem garbage collector is added.

## Repositories and services

- ProjectRepository: catalogue lookup/create/list and source-code resolution.
- ScheduleVersionRepository: metadata lookup/list, hash duplicate check, importing row/source creation and sealing.
- ScheduleDataRepository: batch canonical persistence/reconstruction and diagnostic round trips.
- PersistedScheduleImportService: upload/import/storage/transaction orchestration.
- PersistenceCatalogService: detached DTO queries and canonical Schedule loading.
- StoredAnalysisService: load canonical schedules, then delegate to existing health, DCMA, comparison, milestone, CPM/selected-anchor and reporting services.

Stored comparison versions must belong to the same database Project. Comparison roles BASELINE/CURRENT are assigned by the caller's pair independently of stored version classification, so stored SNAPSHOTs can be compared without extending or altering analytical enums. Analysis Anchors are supplied explicitly and are not persisted or treated as contractual authority.

## API

| Method | Path | Input/result |
| --- | --- | --- |
| POST | /api/projects | JSON project_code/project_name/optional description/active; detached project DTO |
| GET | /api/projects | offset/limit; project DTO list |
| GET | /api/projects/{project_id} | Project UUID metadata |
| POST | /api/projects/{project_id}/schedule-versions | Multipart file, label, optional version_type; immutable successful version DTO |
| GET | /api/projects/{project_id}/schedule-versions | offset/limit; version DTO list |
| GET | /api/schedule-versions/{version_id} | Version metadata/counts/status |
| GET | /api/schedule-versions/{version_id}/health | Existing health result from canonical reload |
| GET | /api/schedule-versions/{version_id}/dcma | Existing DCMA assessment from canonical reload |
| POST | /api/schedule-versions/compare | baseline_version_id/current_version_id; summary and paginated activity/relationship variances |
| POST | /api/schedule-versions/compare-milestones | Version pair; milestone summary/records/findings/comparisons/drivers |
| POST | /api/schedule-versions/{version_id}/analyze-anchor | activity_code or internal_id; mode, optional required_finish/selected_by |
| POST | /api/reports/forensic-change/stored/preview | Version pair, optional analysis_anchor/generated_by; existing serialized forensic report |
| POST | /api/reports/forensic-change/stored/excel | Same body; existing Excel workbook renderer |

The comparison and stored report bodies use UUID strings. Example:

```json
{
  "baseline_version_id": "00000000-0000-0000-0000-000000000001",
  "current_version_id": "00000000-0000-0000-0000-000000000002",
  "analysis_anchor": {"activity_code": "EXPLICIT_MILESTONE", "mode": "CALIBRATION"}
}
```

Omit `analysis_anchor` for an unselected forensic report. INDEPENDENT mode uses the existing caller-required-finish rules; selecting an anchor does not establish completion authority. APIs return controlled 404 missing records, 409 duplicate-source identity (including existing version UUID), 413 over-limit upload, 415 non-XER upload, 422 rejected input/import, or 503 unavailable/configuration/commit-uncertainty cases. SQL/credentials are not included in database-failure responses. Original non-persistent endpoints are unchanged.

## Acceptance evidence

The actual PostgreSQL suite verifies project CRUD service behavior, multiple versions/baselines, hash concurrency and cleanup, pre/post-commit failure handling, immutability across imported tables, native UUID/JSONB, real unique/same-version FK constraints, search indexes, non-TASK UDF isolation, raw scheduling options, diagnostics, calendars, resources/cost fields, and upgrade/downgrade/metadata drift.

The principal round-trip test asserts complete canonical Schedule and diagnostic equality after database reload. It runs the original and reloaded schedules through ScheduleGraph, health, DCMA, milestones, CPM, selected-anchor analysis, baseline/current comparison and deterministic forensic serialization and asserts equal domain results. It independently checks both protected DCMA metrics remain NOT_EVALUATED. Additional tests populate all optional activity dates/constraints and WBS parent paths. The existing baseline/current source fixtures are also imported/reloaded: A1500 removal, A1700 addition and A1200 renamed context survive, while the entire original reporting regression suite remains passing. API tests exercise stored analysis, selected-anchor failure/success, 29-sheet Excel export, JSON preview, duplicate identity, invalid uploads and missing records. No analytic result table is created.

Run tests separately against an explicitly disposable PostgreSQL database:

```powershell
pytest -q -m "not external_xer and not postgres"
$env:POSTGRES_TEST_DATABASE_URL='postgresql+psycopg://test_user:local-password@127.0.0.1:5433/disposable_test_database'
pytest -q -m postgres
```

The PostgreSQL fixture never falls back to SA_DATABASE_URL, production configuration or SQLite. Without POSTGRES_TEST_DATABASE_URL, marked integration tests skip with an explicit reason. The fixture requires permission to create/drop its generated `sa_test_<uuid>` schemas, not to drop databases.

## Files

Created:

- `app/persistence/__init__.py`, `base.py`, `exceptions.py`, `settings.py`, `session.py`
- `app/persistence/models/__init__.py`, `schema.py`
- `app/persistence/mappers/__init__.py`, `codec.py`, `schedule.py`
- `app/persistence/repositories/__init__.py`, `projects.py`, `versions.py`, `schedule_data.py`
- `app/persistence/services/__init__.py`, `storage.py`, `imports.py`, `analyses.py`
- `app/api/persistence.py`
- `alembic.ini`, `migrations/env.py`, `migrations/script.py.mako`, `migrations/versions/e6ff3b33f90b_initial_imported_schedule_schema.py`
- `.env.example`, `docker-compose.yml`
- `tests/conftest_postgres.py`, `tests/persistence_helpers.py`, `tests/test_persistence_unit.py`, `tests/test_persistence_postgres.py`, `tests/test_persistence_api.py`
- `docs/phase7_persistence_contract.md`

Modified: `app/main.py` (router registration), `requirements.txt` (database dependencies), `pyproject.toml` (postgres marker), `.gitignore` (local source storage/environment protection). Pre-existing uncommitted changes from earlier phases were preserved.

## Remaining boundaries and deployment compatibility

- No authentication, tenant access control, frontend, analytical-result storage, source download/edit/delete API, source-retention policy, automatic reconciliation, or backup/restore orchestration is included. Database and source directory must be backed up consistently.
- Full canonical schedules are loaded into memory for existing analyses; initial persistence uses batch writes but is not a streaming/async ingestion worker. A real 23,263-activity database performance benchmark was not run in this increment.
- Narrow Phase 6F raw PROJECT critical-definition evidence is not part of canonical Schedule/Phase 6D typed scheduling options. Stored selected-anchor analysis therefore keeps the existing explicit unknown-evidence/TF-proxy behavior; it does not claim a configured P6 critical-definition match. The original source is retained for future deliberate evidence mapping. No hidden assumption is introduced.
- Only currently canonical imported fields are reconstructed; persistence does not expand importer semantics or revive discarded source fields. Exact original bytes remain available in source storage.
- PostgreSQL 18.4 integration is proven here; Docker PostgreSQL 17 and hosted Supabase connectivity were not executed. The schema uses ordinary PostgreSQL UUID, JSONB, indexes, FKs, transactional DDL and PL/pgSQL triggers, without provider-specific APIs or extensions. Standard PostgreSQL and Supabase-hosted PostgreSQL remain deployment options; deployment-specific credentials/TLS, migration permissions and connection pooling must be configured for the chosen host.
- Earlier Expected Finish/LOE/progress/completion-ambiguity and directional-calculability boundaries remain unchanged. DCMA Critical Path Test and CPLI stay NOT_EVALUATED.

No subsequent phase is automatically started.
