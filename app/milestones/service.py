from __future__ import annotations

from app.comparison.models import ComparisonResult
from app.milestones.analysis import build_milestone_inventory, summarize_milestones
from app.milestones.comparison import compare_milestones
from app.milestones.drivers import candidate_drivers
from app.milestones.models import MilestoneAnalysisResult


class MilestoneAnalysisService:
    def analyze(
        self,
        schedule,
        graph,
        critical_threshold_hours: float = 0.0,
        milestone_limit: int = 100,
        driver_limit: int = 20,
        upstream_limit: int = 200,
        finding_limit: int = 200,
    ) -> MilestoneAnalysisResult:
        records, findings = build_milestone_inventory(schedule, critical_threshold_hours)

        candidate_map = {}
        upstream_inspected = 0
        upstream_truncated = False
        for record in records:
            activity = schedule.activities_by_id.get(record.activity_id)
            if activity is None:
                continue
            drivers, stats = candidate_drivers(
                schedule,
                graph,
                activity,
                record.planned_finish if record.planned_finish is not None else record.planned_start,
                limit=driver_limit,
                upstream_limit=upstream_limit,
            )
            candidate_map[record.activity_code] = tuple(drivers)
            upstream_inspected += stats["upstream_activities"]
            if stats["upstream_activities"] >= upstream_limit:
                upstream_truncated = True

        summary = summarize_milestones(records)

        truncation = {
            "milestones_total": len(records),
            "milestones_returned": min(len(records), milestone_limit),
            "milestones_truncated": len(records) > milestone_limit,
            "findings_total": len(findings),
            "findings_returned": min(len(findings), finding_limit),
            "findings_truncated": len(findings) > finding_limit,
            "candidate_drivers_per_milestone_limit": driver_limit,
            "upstream_activities_inspected": upstream_inspected,
            "upstream_activities_limit": upstream_limit,
            "upstream_activities_truncated": upstream_truncated,
        }

        return MilestoneAnalysisResult(
            schedule=schedule,
            summary=summary,
            milestones=tuple(records[:milestone_limit]),
            findings=tuple(findings[:finding_limit]),
            candidate_drivers=candidate_map,
            truncation=truncation,
        )

    def compare(
        self,
        baseline_schedule,
        current_schedule,
        comparison: ComparisonResult,
        baseline_graph,
        current_graph,
        critical_threshold_hours: float = 0.0,
        milestone_limit: int = 100,
        driver_limit: int = 20,
        upstream_limit: int = 200,
        finding_limit: int = 200,
    ) -> MilestoneAnalysisResult:
        baseline_records, baseline_findings = build_milestone_inventory(
            baseline_schedule, critical_threshold_hours
        )
        current_records, current_findings = build_milestone_inventory(
            current_schedule, critical_threshold_hours
        )

        comparisons, comparison_findings = compare_milestones(comparison)

        all_records = list(current_records)
        candidate_map = {}
        upstream_inspected = 0
        upstream_truncated = False
        for record in current_records:
            activity = current_schedule.activities_by_id.get(record.activity_id)
            if activity is None:
                continue
            drivers, stats = candidate_drivers(
                current_schedule,
                current_graph,
                activity,
                record.planned_finish if record.planned_finish is not None else record.planned_start,
                limit=driver_limit,
                upstream_limit=upstream_limit,
            )
            candidate_map[record.activity_code] = tuple(drivers)
            upstream_inspected += stats["upstream_activities"]
            if stats["upstream_activities"] >= upstream_limit:
                upstream_truncated = True

        summary = summarize_milestones(all_records, comparisons)
        findings = list(baseline_findings) + list(current_findings) + comparison_findings

        truncation = {
            "milestones_total": len(all_records),
            "milestones_returned": min(len(all_records), milestone_limit),
            "milestones_truncated": len(all_records) > milestone_limit,
            "findings_total": len(findings),
            "findings_returned": min(len(findings), finding_limit),
            "findings_truncated": len(findings) > finding_limit,
            "candidate_drivers_per_milestone_limit": driver_limit,
            "upstream_activities_inspected": upstream_inspected,
            "upstream_activities_limit": upstream_limit,
            "upstream_activities_truncated": upstream_truncated,
        }

        return MilestoneAnalysisResult(
            schedule=current_schedule,
            summary=summary,
            milestones=tuple(all_records[:milestone_limit]),
            findings=tuple(findings[:finding_limit]),
            comparisons=tuple(comparisons),
            candidate_drivers=candidate_map,
            truncation=truncation,
        )
