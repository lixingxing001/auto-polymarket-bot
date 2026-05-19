from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .canary_monitor import DEFAULT_MONITOR_REPORT, run_canary_monitor
from .canary_preflight import DEFAULT_CANARY_PREFLIGHT_REPORT, write_canary_preflight_report
from .canary_readiness import DEFAULT_CANARY_REPORT
from .candidate_evidence_progress import (
    DEFAULT_PROGRESS_REPORT,
    write_candidate_evidence_progress_report,
)
from .candidate_change_review import (
    DEFAULT_CHANGE_REVIEW_REPORT,
    write_candidate_change_review_report,
)


DEFAULT_CANARY_WATCH_REPORT = Path("canary_watch_report.md")


def run_canary_watch_once(
    monitor_output_path: Path = DEFAULT_MONITOR_REPORT,
    readiness_output_path: Path = DEFAULT_CANARY_REPORT,
    preflight_output_path: Path = DEFAULT_CANARY_PREFLIGHT_REPORT,
    change_review_output_path: Path = DEFAULT_CHANGE_REVIEW_REPORT,
    evidence_progress_output_path: Path = DEFAULT_PROGRESS_REPORT,
    watch_output_path: Path = DEFAULT_CANARY_WATCH_REPORT,
) -> dict[str, Any]:
    monitor = run_canary_monitor(
        monitor_output_path=monitor_output_path,
        readiness_output_path=readiness_output_path,
    )
    preflight = write_canary_preflight_report(output_path=preflight_output_path)
    change_review = write_candidate_change_review_report(output_path=change_review_output_path)
    evidence_progress = write_candidate_evidence_progress_report(
        output_path=evidence_progress_output_path,
    )
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "monitor": monitor["monitor"],
        "readiness": monitor["readiness"]["readiness"],
        "preflight": preflight["assessment"],
        "change_review": change_review["decision"],
        "evidence_progress": evidence_progress,
    }
    watch_output_path.write_text(render_canary_watch_markdown(report), encoding="utf-8")
    return report


def render_canary_watch_markdown(report: dict[str, Any]) -> str:
    monitor = report["monitor"]
    readiness = report["readiness"]
    preflight = report["preflight"]
    change_review = report["change_review"]
    evidence_progress = report.get("evidence_progress", {})
    progress_summary = evidence_progress.get("summary", {})
    lines = [
        "# Canary Watch Report",
        "",
        f"- checked_at: {report['checked_at']}",
        f"- ready: {monitor['ready']}",
        f"- next_action: {monitor['next_action']}",
        "",
        "## Readiness",
        "",
        f"- blockers: {list(readiness['blockers'])}",
        f"- warnings: {list(readiness['warnings'])}",
        f"- forward_evaluations: {readiness['metrics']['forward_evaluations']}",
        f"- forward_trades: {readiness['metrics']['forward_trades']}",
        f"- forward_win_rate: {readiness['metrics']['forward_win_rate']}",
        f"- forward_total_pnl_usd: {readiness['metrics']['forward_total_pnl_usd']}",
        f"- next_change_review_gap: {readiness['metrics']['next_change_review_gap']}",
        "",
        "## Preflight",
        "",
        f"- status: {preflight['status']}",
        f"- real_adapter_review_allowed: {preflight['real_adapter_review_allowed']}",
        f"- blockers: {list(preflight['blockers'])}",
        "",
        "## Candidate change review",
        "",
        f"- status: {change_review['status']}",
        f"- selected_candidate_id: {_display_candidate_id(change_review['selected_candidate_id'])}",
        f"- change_allowed: {change_review['change_allowed']}",
        f"- blockers: {list(change_review['blockers'])}",
        f"- warnings: {list(change_review['warnings'])}",
        "",
        "## Candidate evidence progress",
        "",
        f"- next_review_candidate_id: {evidence_progress.get('next_review_candidate_id', 'none')}",
        f"- review_ready_candidates: {progress_summary.get('review_ready_candidates', [])}",
        f"- change_quality_passed_candidates: {progress_summary.get('change_quality_passed_candidates', [])}",
        f"- needs_divergent_windows: {progress_summary.get('needs_divergent_windows', [])}",
        f"- waiting_for_first_divergence: {progress_summary.get('waiting_for_first_divergence', [])}",
        "",
        "## Boundary",
        "",
        "This watchdog refreshes reports only. It does not submit orders and it does not read private keys.",
    ]
    return "\n".join(lines) + "\n"


def run_loop(
    iterations: int,
    interval_seconds: float,
    continue_on_error: bool,
) -> None:
    index = 0
    while iterations == 0 or index < iterations:
        try:
            report = run_canary_watch_once()
            print(report, flush=True)
        except Exception as exc:  # noqa: BLE001
            print(
                {
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                    "error": type(exc).__name__,
                    "message": str(exc),
                },
                file=sys.stderr,
                flush=True,
            )
            if not continue_on_error:
                raise
        index += 1
        if iterations == 0 or index < iterations:
            time.sleep(interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--interval-seconds", type=float, default=600.0)
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args()
    run_loop(
        iterations=args.iterations,
        interval_seconds=args.interval_seconds,
        continue_on_error=args.continue_on_error,
    )


def _display_candidate_id(candidate_id: str) -> str:
    return candidate_id or "none"


if __name__ == "__main__":
    main()
