from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .candidate_strategies import is_candidate_active, load_candidate_registry
from .recent_loss_diagnostics import build_recent_loss_diagnostics_report


DEFAULT_REGISTRY = Path("strategy_candidates.csv")
DEFAULT_GENERATION_REPORT = Path("candidate_generation_report.md")


@dataclass(frozen=True)
class CandidateProposal:
    candidate_id: str
    filter_kind: str
    rationale: str
    source_dimension: str
    source_bucket: str
    source_trades: int
    source_win_rate: float
    source_total_pnl_usd: float
    action: str
    register_command: str


def build_candidate_generation_report(
    registry_path: Path = DEFAULT_REGISTRY,
    recent_loss_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    recent_loss_report = recent_loss_report or build_recent_loss_diagnostics_report()
    registry = load_candidate_registry(registry_path)
    proposals = build_candidate_proposals(
        recent_loss_report=recent_loss_report,
        active_filter_kinds={
            candidate.filter_kind
            for candidate in registry.values()
            if is_candidate_active(candidate)
        },
        has_active_confidence_070=any(
            is_candidate_active(candidate) and candidate.min_confidence >= 0.70
            for candidate in registry.values()
        ),
        existing_candidate_ids=set(registry),
    )
    return {
        "target": {
            "forward_win_rate_goal": 0.60,
            "live_order_goal": "canary_after_readiness_and_explicit_lee_authorization",
        },
        "current_forward": recent_loss_report["ledger_summary"],
        "diagnostic_flags": recent_loss_report["flags"],
        "proposals": [proposal.__dict__ for proposal in proposals],
    }


def build_candidate_proposals(
    recent_loss_report: dict[str, Any],
    active_filter_kinds: set[str],
    has_active_confidence_070: bool,
    existing_candidate_ids: set[str] | None = None,
) -> tuple[CandidateProposal, ...]:
    existing_candidate_ids = existing_candidate_ids or set()
    proposals: list[CandidateProposal] = []
    for slice_item in recent_loss_report["worst_slices"]:
        if not _slice_is_bad_enough(slice_item):
            continue
        dimension = slice_item["dimension"]
        bucket = str(slice_item["bucket"])
        if (
            dimension == "trade_vs_5m_momentum"
            and bucket == "against_momentum"
        ):
            active = "avoid_trade_against_5m_momentum" in active_filter_kinds
            base_candidate_id = "avoid_trade_against_5m_momentum"
            proposals.append(
                _proposal(
                    candidate_id=(
                        base_candidate_id
                        if active
                        else _next_available_candidate_id(
                            base_candidate_id,
                            existing_candidate_ids,
                        )
                    ),
                    filter_kind="avoid_trade_against_5m_momentum",
                    slice_item=slice_item,
                    rationale="Recent losses cluster in trades placed against 5 minute BTC momentum.",
                    action=(
                        "collect_prospective_evidence"
                        if active
                        else "register_prospectively"
                    ),
                )
            )
        if (
            dimension == "trade_vs_1m_momentum"
            and bucket == "against_momentum"
        ):
            active = "avoid_trade_against_1m_momentum" in active_filter_kinds
            base_candidate_id = "avoid_trade_against_1m_momentum"
            proposals.append(
                _proposal(
                    candidate_id=(
                        base_candidate_id
                        if active
                        else _next_available_candidate_id(
                            base_candidate_id,
                            existing_candidate_ids,
                        )
                    ),
                    filter_kind="avoid_trade_against_1m_momentum",
                    slice_item=slice_item,
                    rationale="Recent losses cluster in trades placed against 1 minute BTC momentum.",
                    action=(
                        "collect_prospective_evidence"
                        if active
                        else "register_prospectively"
                    ),
                )
            )
        if (
            dimension == "confidence"
            and bucket == "0.65-0.70"
        ):
            proposals.append(
                _proposal(
                    candidate_id=(
                        "confidence_070"
                        if has_active_confidence_070
                        else _next_available_candidate_id(
                            "confidence_070",
                            existing_candidate_ids,
                        )
                    ),
                    filter_kind="none",
                    slice_item=slice_item,
                    rationale="Recent losses cluster in the 0.65 to 0.70 confidence bucket.",
                    extra_args=" --min-confidence 0.70",
                    action=(
                        "collect_prospective_evidence"
                        if has_active_confidence_070
                        else "register_prospectively"
                    ),
                )
            )
    return tuple(_dedupe_by_candidate_id(proposals))


def render_candidate_generation_markdown(report: dict[str, Any]) -> str:
    current = report["current_forward"]
    lines = [
        "# Candidate Generation Report",
        "",
        "## Target",
        "",
        f"- forward_win_rate_goal: {report['target']['forward_win_rate_goal']:.0%}",
        f"- live_order_goal: {report['target']['live_order_goal']}",
        "",
        "## Current forward state",
        "",
        f"- forward_evaluations: {current['evaluations']}",
        f"- forward_trades: {current['traded_rows']}",
        f"- forward_win_rate: {current['win_rate']:.1%}",
        f"- forward_total_pnl_usd: {current['total_pnl_usd']:.2f}",
        "",
        "## Diagnostic flags",
        "",
        *(_render_items(report["diagnostic_flags"])),
        "",
        "## Proposed next candidates",
        "",
    ]
    if not report["proposals"]:
        lines.append("- none")
    else:
        lines.extend(
            [
                "| candidate_id | filter_kind | action | source | trades | win_rate | pnl |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for proposal in report["proposals"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        proposal["candidate_id"],
                        proposal["filter_kind"],
                        proposal["action"],
                        f"{proposal['source_dimension']}={proposal['source_bucket']}",
                        str(proposal["source_trades"]),
                        f"{proposal['source_win_rate']:.1%}",
                        f"{proposal['source_total_pnl_usd']:.2f}",
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Next commands",
            "",
        ]
    )
    for proposal in report["proposals"]:
        lines.append(f"- `{proposal['register_command']}`")
    if not report["proposals"]:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This report proposes prospective candidates only. It does not promote parameters, enable live trading or submit orders.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_candidate_generation_report(
    output_path: Path = DEFAULT_GENERATION_REPORT,
    registry_path: Path = DEFAULT_REGISTRY,
) -> dict[str, Any]:
    report = build_candidate_generation_report(registry_path=registry_path)
    output_path.write_text(render_candidate_generation_markdown(report), encoding="utf-8")
    return report


def _slice_is_bad_enough(slice_item: dict[str, Any]) -> bool:
    return (
        slice_item["trades"] >= 3
        and slice_item["win_rate"] < 0.45
        and slice_item["total_pnl_usd"] < 0.0
    )


def _proposal(
    candidate_id: str,
    filter_kind: str,
    slice_item: dict[str, Any],
    rationale: str,
    extra_args: str = "",
    action: str = "register_prospectively",
) -> CandidateProposal:
    if action == "register_prospectively":
        register_command = (
            "python -m btc5m_bot.strategy_candidate_cli register"
            f" --candidate-id {candidate_id}"
            f" --description \"{candidate_id}\""
            f" --rationale \"{rationale}\""
            f" --filter-kind {filter_kind}"
            f"{extra_args}"
        )
    else:
        register_command = (
            "python -m btc5m_bot.strategy_candidate_cli compare"
            f" --candidate-id {candidate_id}"
        )
    return CandidateProposal(
        candidate_id=candidate_id,
        filter_kind=filter_kind,
        rationale=rationale,
        source_dimension=slice_item["dimension"],
        source_bucket=str(slice_item["bucket"]),
        source_trades=int(slice_item["trades"]),
        source_win_rate=float(slice_item["win_rate"]),
        source_total_pnl_usd=float(slice_item["total_pnl_usd"]),
        action=action,
        register_command=register_command,
    )


def _dedupe_by_candidate_id(
    proposals: list[CandidateProposal],
) -> list[CandidateProposal]:
    by_id: dict[str, CandidateProposal] = {}
    for proposal in proposals:
        existing = by_id.get(proposal.candidate_id)
        if existing is None or proposal.source_total_pnl_usd < existing.source_total_pnl_usd:
            by_id[proposal.candidate_id] = proposal
    return sorted(
        by_id.values(),
        key=lambda item: (
            item.source_win_rate,
            item.source_total_pnl_usd,
            -item.source_trades,
        ),
    )


def _next_available_candidate_id(base: str, existing_ids: set[str]) -> str:
    if base not in existing_ids:
        return base
    index = 2
    while f"{base}_v{index}" in existing_ids:
        index += 1
    return f"{base}_v{index}"


def _render_items(items: tuple[str, ...] | list[str]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]
