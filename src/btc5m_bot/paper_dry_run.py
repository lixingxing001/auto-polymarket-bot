from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .execution_safety import (
    ExecutionSafetyConfig,
    ProposedOrder,
    assess_execution_safety,
    load_execution_ledger_rows,
    parse_execution_ledger_rows,
    summarize_execution_ledger,
)
from .paper_signal import generate_paper_signal
from .strategy_guardrails import (
    assess_strategy_guardrails,
    load_forward_ledger_rows,
    summarize_forward_ledger,
)


DEFAULT_DRY_RUN_OUTPUT = Path("data/paper_dry_runs.csv")
DEFAULT_FORWARD_LEDGER = Path("data/forward_snapshot_evaluations.csv")
DEFAULT_EXECUTION_LEDGER = Path("data/live_execution_ledger.csv")


def build_proposed_order_from_signal(signal: dict[str, Any]) -> ProposedOrder | None:
    decision = str(signal.get("decision", "HOLD")).upper()
    if decision == "HOLD":
        return None
    if decision not in {"UP", "DOWN"}:
        raise ValueError(f"unsupported paper decision: {decision}")

    price_key = "up_ask" if decision == "UP" else "down_ask"
    liquidity_key = "up_liquidity_usd" if decision == "UP" else "down_liquidity_usd"
    probability = _required_float(signal, "prob_up")
    if decision == "DOWN":
        probability = 1.0 - probability

    return ProposedOrder(
        slug=str(signal["slug"]),
        outcome=decision,
        price=_required_float(signal, price_key),
        stake_usd=_required_float(signal, "size_usd"),
        edge=_required_float(signal, "edge"),
        probability=probability,
        available_liquidity_usd=_required_float(signal, liquidity_key),
        seconds_to_close=int(signal["seconds_to_close"]),
        client_order_id=build_client_order_id(signal, decision),
    )


def build_client_order_id(signal: dict[str, Any], decision: str) -> str:
    timestamp = str(signal.get("timestamp", "unknown")).replace(":", "").replace("+", "")
    slug = str(signal.get("slug", "unknown"))
    return f"paper-dry-run-{slug}-{decision.lower()}-{timestamp}"


def assess_signal_execution_preflight(
    signal: dict[str, Any],
    forward_ledger_rows: list[dict[str, str]],
    execution_ledger_rows: list[dict[str, str]],
    config: ExecutionSafetyConfig | None = None,
) -> dict[str, Any]:
    forward_summary = summarize_forward_ledger(forward_ledger_rows)
    guardrails = assess_strategy_guardrails(forward_summary)
    execution_summary = summarize_execution_ledger(
        parse_execution_ledger_rows(execution_ledger_rows)
    )
    proposed_order = build_proposed_order_from_signal(signal)
    assessment = assess_execution_safety(
        forward_summary=forward_summary,
        guardrail_assessment=guardrails,
        ledger_summary=execution_summary,
        proposed_order=proposed_order,
        config=config,
    )
    return {
        "actionable_signal": proposed_order is not None,
        "order_send_allowed": proposed_order is not None and assessment.allowed,
        "proposed_order": asdict(proposed_order) if proposed_order is not None else None,
        "assessment": asdict(assessment),
        "forward_ledger": asdict(forward_summary),
        "guardrails": guardrails,
        "execution_ledger": asdict(execution_summary),
    }


def run_signal_execution_preflight(
    signal: dict[str, Any],
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER,
    execution_ledger_path: Path = DEFAULT_EXECUTION_LEDGER,
    config: ExecutionSafetyConfig | None = None,
) -> dict[str, Any]:
    return assess_signal_execution_preflight(
        signal=signal,
        forward_ledger_rows=load_forward_ledger_rows(forward_ledger_path),
        execution_ledger_rows=load_execution_ledger_rows(execution_ledger_path),
        config=config,
    )


def generate_paper_dry_run(
    config: ExecutionSafetyConfig | None = None,
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER,
    execution_ledger_path: Path = DEFAULT_EXECUTION_LEDGER,
) -> dict[str, Any]:
    signal = generate_paper_signal()
    preflight = run_signal_execution_preflight(
        signal=signal,
        forward_ledger_path=forward_ledger_path,
        execution_ledger_path=execution_ledger_path,
        config=config,
    )
    return {
        **signal,
        "execution_preflight": preflight,
    }


def append_dry_run(path: Path, dry_run: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    preflight = dry_run.get("execution_preflight", {})
    assessment = preflight.get("assessment", {})
    row = {
        "timestamp": dry_run.get("timestamp", ""),
        "slug": dry_run.get("slug", ""),
        "title": dry_run.get("title", ""),
        "seconds_to_close": dry_run.get("seconds_to_close", ""),
        "prob_up": dry_run.get("prob_up", ""),
        "decision": dry_run.get("decision", ""),
        "edge": dry_run.get("edge", ""),
        "size_usd": dry_run.get("size_usd", ""),
        "reason": dry_run.get("reason", ""),
        "execution_preflight_allowed": preflight.get("order_send_allowed", ""),
        "execution_preflight_reasons_json": json.dumps(
            assessment.get("reasons", []),
            separators=(",", ":"),
        ),
        "execution_preflight_warnings_json": json.dumps(
            assessment.get("warnings", []),
            separators=(",", ":"),
        ),
        "proposed_order_json": json.dumps(
            preflight.get("proposed_order"),
            separators=(",", ":"),
            sort_keys=True,
        ),
        "execution_metrics_json": json.dumps(
            assessment.get("metrics", {}),
            separators=(",", ":"),
            sort_keys=True,
        ),
        "features_json": json.dumps(
            dry_run.get("features", {}),
            separators=(",", ":"),
            sort_keys=True,
        ),
    }
    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def _required_float(payload: dict[str, Any], key: str) -> float:
    value = payload.get(key)
    if value in {None, ""}:
        raise ValueError(f"missing required signal field: {key}")
    return float(value)
