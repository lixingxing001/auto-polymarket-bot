from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .strategy_guardrails import (
    assess_strategy_guardrails,
    load_forward_ledger_rows,
    summarize_forward_ledger,
)


DEFAULT_INTENT_EVENT_LOG = Path("data/order_intent_events.csv")
DEFAULT_ATTEMPT_LOG = Path("data/live_execution_attempts.csv")
DEFAULT_FORWARD_LEDGER = Path("data/forward_snapshot_evaluations.csv")
DEFAULT_REPORT = Path("execution_health_report.md")


@dataclass(frozen=True)
class ExecutionHealthSummary:
    intent_events: int
    created_intents: int
    terminal_intents: int
    attempts: int
    accepted_attempts: int
    rejected_attempts: int
    status_counts: dict[str, int] = field(default_factory=dict)
    paper_reason_counts: dict[str, int] = field(default_factory=dict)
    safety_reason_counts: dict[str, int] = field(default_factory=dict)
    safety_warning_counts: dict[str, int] = field(default_factory=dict)
    attempt_reason_counts: dict[str, int] = field(default_factory=dict)
    actionable_signals: int = 0
    order_send_allowed: int = 0


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summarize_execution_health(
    intent_event_rows: list[dict[str, str]],
    attempt_rows: list[dict[str, str]],
) -> ExecutionHealthSummary:
    status_counts: dict[str, int] = {}
    paper_reason_counts: dict[str, int] = {}
    safety_reason_counts: dict[str, int] = {}
    safety_warning_counts: dict[str, int] = {}
    attempt_reason_counts: dict[str, int] = {}
    actionable_signals = 0
    order_send_allowed = 0

    for row in intent_event_rows:
        status = row.get("status", "")
        if status:
            status_counts[status] = status_counts.get(status, 0) + 1
        details = _details(row)
        paper_reason = str(details.get("paper_reason", ""))
        if paper_reason:
            paper_reason_counts[paper_reason] = paper_reason_counts.get(paper_reason, 0) + 1
        if details.get("actionable_signal") is True:
            actionable_signals += 1
        if details.get("order_send_allowed") is True:
            order_send_allowed += 1
        for reason in details.get("safety_reasons", ()):
            safety_reason_counts[reason] = safety_reason_counts.get(reason, 0) + 1
        for warning in details.get("safety_warnings", ()):
            safety_warning_counts[warning] = safety_warning_counts.get(warning, 0) + 1

    for row in attempt_rows:
        reason = row.get("reason", "")
        if reason:
            attempt_reason_counts[reason] = attempt_reason_counts.get(reason, 0) + 1
        for reason in _json_list(row.get("safety_reasons_json", "[]")):
            safety_reason_counts[reason] = safety_reason_counts.get(reason, 0) + 1
        for warning in _json_list(row.get("safety_warnings_json", "[]")):
            safety_warning_counts[warning] = safety_warning_counts.get(warning, 0) + 1

    attempts = len(attempt_rows)
    accepted_attempts = sum(1 for row in attempt_rows if row.get("accepted") == "True")
    return ExecutionHealthSummary(
        intent_events=len(intent_event_rows),
        created_intents=status_counts.get("created", 0),
        terminal_intents=len(intent_event_rows) - status_counts.get("created", 0),
        attempts=attempts,
        accepted_attempts=accepted_attempts,
        rejected_attempts=attempts - accepted_attempts,
        status_counts=dict(sorted(status_counts.items())),
        paper_reason_counts=dict(sorted(paper_reason_counts.items(), key=lambda item: (-item[1], item[0]))),
        safety_reason_counts=dict(sorted(safety_reason_counts.items(), key=lambda item: (-item[1], item[0]))),
        safety_warning_counts=dict(sorted(safety_warning_counts.items(), key=lambda item: (-item[1], item[0]))),
        attempt_reason_counts=dict(sorted(attempt_reason_counts.items(), key=lambda item: (-item[1], item[0]))),
        actionable_signals=actionable_signals,
        order_send_allowed=order_send_allowed,
    )


def build_execution_health_report(
    intent_event_path: Path = DEFAULT_INTENT_EVENT_LOG,
    attempt_log_path: Path = DEFAULT_ATTEMPT_LOG,
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER,
) -> dict[str, Any]:
    summary = summarize_execution_health(
        intent_event_rows=load_csv_rows(intent_event_path),
        attempt_rows=load_csv_rows(attempt_log_path),
    )
    forward_summary = summarize_forward_ledger(load_forward_ledger_rows(forward_ledger_path))
    guardrails = assess_strategy_guardrails(forward_summary)
    return {
        "execution_health": summary.__dict__,
        "forward_ledger": forward_summary.__dict__,
        "guardrails": guardrails,
        "diagnosis": diagnose_execution_health(summary, guardrails),
    }


def diagnose_execution_health(
    summary: ExecutionHealthSummary,
    guardrails: dict[str, Any],
) -> list[str]:
    diagnosis: list[str] = []
    if summary.created_intents == 0:
        diagnosis.append("no_intents_recorded")
    if summary.actionable_signals == 0 and summary.created_intents > 0:
        diagnosis.append("paper_signal_not_actionable")
    if summary.order_send_allowed == 0 and summary.actionable_signals > 0:
        diagnosis.append("execution_safety_blocks_actionable_signals")
    if summary.accepted_attempts == 0 and summary.attempts > 0:
        diagnosis.append("no_attempts_accepted")
    if guardrails.get("stage") != "change_review_ready":
        diagnosis.append(f"guardrail_stage_{guardrails.get('stage', 'unknown')}")
    return diagnosis


def render_execution_health_markdown(report: dict[str, Any]) -> str:
    health = report["execution_health"]
    forward = report["forward_ledger"]
    guardrails = report["guardrails"]
    lines = [
        "# Execution Health Report",
        "",
        "## Summary",
        "",
        f"- intent_events: {health['intent_events']}",
        f"- created_intents: {health['created_intents']}",
        f"- terminal_intents: {health['terminal_intents']}",
        f"- attempts: {health['attempts']}",
        f"- accepted_attempts: {health['accepted_attempts']}",
        f"- rejected_attempts: {health['rejected_attempts']}",
        f"- actionable_signals: {health['actionable_signals']}",
        f"- order_send_allowed: {health['order_send_allowed']}",
        "",
        "## Diagnosis",
        "",
    ]
    lines.extend(f"- {item}" for item in report["diagnosis"])
    lines.extend(
        [
            "",
            "## Top blockers",
            "",
            "### Paper reasons",
            "",
            *(_render_counts(health["paper_reason_counts"])),
            "",
            "### Safety reasons",
            "",
            *(_render_counts(health["safety_reason_counts"])),
            "",
            "### Attempt reasons",
            "",
            *(_render_counts(health["attempt_reason_counts"])),
            "",
            "## Forward gate",
            "",
            f"- evaluations: {forward['evaluations']}",
            f"- trades: {forward['traded_rows']}",
            f"- wins: {forward['wins']}",
            f"- losses: {forward['losses']}",
            f"- win_rate: {forward['win_rate']}",
            f"- total_pnl_usd: {forward['total_pnl_usd']}",
            f"- guardrail_stage: {guardrails['stage']}",
            f"- next_review_gap: {guardrails['next_review_gap']}",
            f"- next_change_review_gap: {guardrails['next_change_review_gap']}",
            "",
            "## Interpretation",
            "",
            "The execution layer is currently doing its job: it records why orders do not progress. The next improvement should be based on the largest blocker, not on gut feel.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_execution_health_report(
    output_path: Path = DEFAULT_REPORT,
    intent_event_path: Path = DEFAULT_INTENT_EVENT_LOG,
    attempt_log_path: Path = DEFAULT_ATTEMPT_LOG,
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER,
) -> dict[str, Any]:
    report = build_execution_health_report(
        intent_event_path=intent_event_path,
        attempt_log_path=attempt_log_path,
        forward_ledger_path=forward_ledger_path,
    )
    output_path.write_text(render_execution_health_markdown(report), encoding="utf-8")
    return report


def _render_counts(counts: dict[str, int]) -> list[str]:
    if not counts:
        return ["- none"]
    return [f"- {key}: {value}" for key, value in counts.items()]


def _details(row: dict[str, str]) -> dict[str, Any]:
    raw = row.get("details_json", "{}")
    if not raw:
        return {}
    return json.loads(raw)


def _json_list(raw: str) -> list[str]:
    if not raw:
        return []
    parsed = json.loads(raw)
    return list(parsed) if isinstance(parsed, list) else []
