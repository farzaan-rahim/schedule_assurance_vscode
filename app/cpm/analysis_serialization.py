"""Schedule-free JSON/UI contract for explicit selected analyses."""
from app.reporting.serialization import to_json_value


def analysis_payload(analysis):
    return to_json_value(dict(schema_version='1.0',analysis_anchor=analysis.anchor,
        completion_authority_status=analysis.anchor.contractual_authority_status,
        mode=analysis.mode,summary=analysis.summary,activity_results=analysis.cpm_result.activity_results,
        directional_availability=dict(activities=analysis.activity_dispositions,relationships=analysis.relationship_dispositions),
        controlling_paths=analysis.cpm_result.critical_paths,path_statistics=analysis.cpm_result.path_statistics,
        path_status=analysis.path_status,blocked_boundaries=analysis.blocked_boundaries,comparisons=analysis.comparisons,
        diagnostics=analysis.diagnostics,dcma_critical_path_test='NOT_EVALUATED',cpli='NOT_EVALUATED'))
