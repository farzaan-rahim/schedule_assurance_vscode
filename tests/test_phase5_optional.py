from pathlib import Path

from app.importers.schedule_mapper import ScheduleMapper
from app.importers.xer_parser import XERParser
from app.services.schedule_import import ScheduleImportService


FIXTURE = Path(__file__).with_name("phase5_optional.xer")


def test_optional_tables_parse_and_map():
    tables = XERParser().parse(FIXTURE)
    for table_name in ("RSRC", "TASKRSRC", "ACTVTYPE", "ACTVCODE", "TASKACTV", "UDFTYPE", "UDFVALUE"):
        assert table_name in tables
    assert len(tables["RSRC"]) == 2
    assert len(tables["TASKRSRC"]) == 2
    assert len(tables["ACTVTYPE"]) == 2
    assert len(tables["ACTVCODE"]) == 3
    assert len(tables["TASKACTV"]) == 3
    assert len(tables["UDFTYPE"]) == 4
    assert len(tables["UDFVALUE"]) == 4


def test_resources_assignments_and_lookups():
    result = ScheduleImportService().import_file(FIXTURE)
    assert result.succeeded
    schedule = result.schedule
    assert schedule is not None

    assert result.statistics.resources == 2
    assert result.statistics.resource_assignments == 2
    assert len(schedule.resources) == 2
    assert len(schedule.resource_assignments) == 2

    resource = schedule.resources["R1"]
    assert resource.resource_code == "ENG"
    assert resource.resource_name == "Engineer"
    assert resource.employee_id == "EMP1"

    assignments = schedule.get_resource_assignments("1")
    assert len(assignments) == 2
    assert assignments[0].target_quantity == 16
    assert assignments[0].planned_cost == 1168


def test_activity_code_types_values_and_assignments():
    schedule = ScheduleMapper().map(XERParser().parse(FIXTURE))

    assert len(schedule.activity_code_types) == 2
    assert len(schedule.activity_code_values) == 3
    assert len(schedule.activity_code_assignments) == 3

    mechanical = schedule.get_activity_code("1", "Discipline")
    area = schedule.get_activity_code("1", "Area")
    assert [value.short_name for value in mechanical] == ["MECH"]
    assert [value.short_name for value in area] == ["NORTH"]


def test_udf_text_numeric_date_and_non_activity_values():
    schedule = ScheduleMapper().map(XERParser().parse(FIXTURE))

    assert len(schedule.udf_definitions) == 4
    assert len(schedule.udf_values) == 4

    activity_udfs = schedule.get_activity_udf_values("1")
    assert len(activity_udfs) == 3

    values = {schedule.udf_definitions[value.udf_type_id].name: value for value in activity_udfs}
    assert values["Text Field"].text_value == "Alpha"
    assert values["Numeric Field"].numeric_value == 123.5
    assert values["Date Field"].date_value is not None


def test_optional_table_absence_is_backward_compatible():
    result = ScheduleImportService().import_file("sample_data/sample_current.xer")
    assert result.succeeded
    assert result.schedule is not None
    assert result.statistics.resources == 0
    assert result.statistics.resource_assignments == 0
    assert result.statistics.activity_code_types == 0
    assert result.statistics.activity_code_values == 0
    assert result.statistics.activity_code_assignments == 0
    assert result.statistics.udf_definitions == 0
    assert result.statistics.udf_values == 0


def test_nrg00800_optional_mapping_counts():
    result = ScheduleImportService().import_file("sample_data/NRG00800.xer")
    assert result.succeeded
    assert result.schedule is not None

    assert result.statistics.resources >= 9
    assert result.statistics.resource_assignments >= 164
    assert result.statistics.activity_code_types >= 11
    assert result.statistics.activity_code_values >= 448
    assert result.statistics.activity_code_assignments >= 1433
    assert result.statistics.udf_definitions >= 7
    assert result.statistics.udf_values >= 7


def test_malformed_optional_numeric_value_diagnostic():
    tables = XERParser().parse(FIXTURE)
    tables["TASKRSRC"][0]["target_qty"] = "not-a-number"
    from app.importers.models import ImportDiagnostic

    diagnostics = []
    schedule = ScheduleMapper().map(tables, diagnostics)
    assert diagnostics
    assert any(d.code == "invalid_number" and d.table == "TASKRSRC" for d in diagnostics)
    assert schedule.resource_assignments["A1"].target_quantity is None
