from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .candidate_strategies import CandidateStrategy
from .execution_backtest import ExecutionBacktestConfig
from .models import FeatureVector
from .strategy_guardrails import ACTIVE_STRATEGY_PARAMETERS


DEFAULT_ACTIVE_STRATEGY_STATE = Path("data/active_strategy_state.json")


@dataclass(frozen=True)
class ActiveStrategyState:
    mode: str
    source_candidate_id: str
    description: str
    rationale: str
    activated_at: datetime
    live_trading_enabled: bool
    min_confidence: float
    min_edge: float
    stake_usd: float
    max_fill_delay_seconds: int
    filter_kind: str = "none"
    min_abs_return_1m: float | None = None
    min_abs_return_5m: float | None = None
    max_abs_return_5m: float | None = None
    min_abs_distance_to_barrier_bps: float | None = None
    max_abs_distance_to_barrier_bps: float | None = None


def default_active_strategy_state(now: datetime | None = None) -> ActiveStrategyState:
    now = now or datetime.now(timezone.utc)
    return ActiveStrategyState(
        mode="paper",
        source_candidate_id="baseline",
        description="Baseline active paper strategy",
        rationale="Default strategy parameters compiled into the bot",
        activated_at=now,
        live_trading_enabled=False,
        min_confidence=ACTIVE_STRATEGY_PARAMETERS.min_confidence,
        min_edge=ACTIVE_STRATEGY_PARAMETERS.min_edge,
        stake_usd=ACTIVE_STRATEGY_PARAMETERS.stake_usd,
        max_fill_delay_seconds=ACTIVE_STRATEGY_PARAMETERS.max_fill_delay_seconds,
    )


def active_strategy_state_from_candidate(
    candidate: CandidateStrategy,
    now: datetime | None = None,
) -> ActiveStrategyState:
    now = now or datetime.now(timezone.utc)
    return ActiveStrategyState(
        mode="paper",
        source_candidate_id=candidate.candidate_id,
        description=candidate.description,
        rationale=candidate.rationale,
        activated_at=now,
        live_trading_enabled=False,
        min_confidence=candidate.min_confidence,
        min_edge=candidate.min_edge,
        stake_usd=candidate.stake_usd,
        max_fill_delay_seconds=candidate.max_fill_delay_seconds,
        filter_kind=candidate.filter_kind,
        min_abs_return_1m=candidate.min_abs_return_1m,
        min_abs_return_5m=candidate.min_abs_return_5m,
        max_abs_return_5m=candidate.max_abs_return_5m,
        min_abs_distance_to_barrier_bps=candidate.min_abs_distance_to_barrier_bps,
        max_abs_distance_to_barrier_bps=candidate.max_abs_distance_to_barrier_bps,
    )


def load_optional_active_strategy_state(path: Path = DEFAULT_ACTIVE_STRATEGY_STATE) -> ActiveStrategyState | None:
    if not path.exists():
        return None
    return parse_active_strategy_state(json.loads(path.read_text(encoding="utf-8")))


def load_active_strategy_state(path: Path = DEFAULT_ACTIVE_STRATEGY_STATE) -> ActiveStrategyState:
    return load_optional_active_strategy_state(path) or default_active_strategy_state()


def write_active_strategy_state(
    path: Path,
    state: ActiveStrategyState,
) -> ActiveStrategyState:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **asdict(state),
        "activated_at": state.activated_at.isoformat(),
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return state


def parse_active_strategy_state(payload: dict[str, Any]) -> ActiveStrategyState:
    return ActiveStrategyState(
        mode=str(payload.get("mode", "paper")),
        source_candidate_id=str(payload["source_candidate_id"]),
        description=str(payload.get("description", "")),
        rationale=str(payload.get("rationale", "")),
        activated_at=datetime.fromisoformat(str(payload["activated_at"])),
        live_trading_enabled=bool(payload.get("live_trading_enabled", False)),
        min_confidence=float(payload["min_confidence"]),
        min_edge=float(payload["min_edge"]),
        stake_usd=float(payload["stake_usd"]),
        max_fill_delay_seconds=int(payload["max_fill_delay_seconds"]),
        filter_kind=str(payload.get("filter_kind", "none") or "none"),
        min_abs_return_1m=_optional_float(payload.get("min_abs_return_1m")),
        min_abs_return_5m=_optional_float(payload.get("min_abs_return_5m")),
        max_abs_return_5m=_optional_float(payload.get("max_abs_return_5m")),
        min_abs_distance_to_barrier_bps=_optional_float(
            payload.get("min_abs_distance_to_barrier_bps")
        ),
        max_abs_distance_to_barrier_bps=_optional_float(
            payload.get("max_abs_distance_to_barrier_bps")
        ),
    )


def active_strategy_to_execution_config(state: ActiveStrategyState) -> ExecutionBacktestConfig:
    return ExecutionBacktestConfig(
        min_confidence=state.min_confidence,
        min_edge=state.min_edge,
        stake_usd=state.stake_usd,
        max_fill_delay_seconds=state.max_fill_delay_seconds,
    )


def active_strategy_allows_trade(
    state: ActiveStrategyState,
    features: FeatureVector,
    decision: str,
) -> bool:
    if not active_strategy_allows_features(state, features):
        return False
    if decision == "HOLD":
        return True
    if state.filter_kind == "avoid_trade_against_1m_momentum":
        return not _trade_against_momentum(decision, features.return_1m)
    if state.filter_kind == "avoid_trade_against_5m_momentum":
        return not _trade_against_momentum(decision, features.return_5m)
    return True


def active_strategy_allows_features(
    state: ActiveStrategyState,
    features: FeatureVector,
) -> bool:
    if state.filter_kind == "none":
        return True
    if state.filter_kind == "avoid_low_momentum_near_barrier":
        min_abs_return_1m = state.min_abs_return_1m or 0.0
        min_abs_distance = state.min_abs_distance_to_barrier_bps or 0.0
        return not (
            abs(features.return_1m) <= min_abs_return_1m
            and abs(features.distance_to_barrier_bps) <= min_abs_distance
        )
    if state.filter_kind == "avoid_mid_abs_return_5m":
        min_abs_return_5m = state.min_abs_return_5m
        max_abs_return_5m = state.max_abs_return_5m
        if min_abs_return_5m is None or max_abs_return_5m is None:
            raise ValueError("mid return filter requires min and max abs return 5m")
        abs_return_5m = abs(features.return_5m)
        return not (min_abs_return_5m < abs_return_5m <= max_abs_return_5m)
    if state.filter_kind == "avoid_mid_distance_to_barrier_bps":
        min_abs_distance = state.min_abs_distance_to_barrier_bps
        max_abs_distance = state.max_abs_distance_to_barrier_bps
        if min_abs_distance is None or max_abs_distance is None:
            raise ValueError("mid distance filter requires min and max abs distance")
        abs_distance = abs(features.distance_to_barrier_bps)
        return not (min_abs_distance < abs_distance <= max_abs_distance)
    if state.filter_kind in {
        "avoid_trade_against_1m_momentum",
        "avoid_trade_against_5m_momentum",
    }:
        return True
    raise ValueError(f"unsupported active strategy filter: {state.filter_kind}")


def _trade_against_momentum(decision: str, momentum: float) -> bool:
    if momentum == 0.0:
        return False
    if decision == "UP":
        return momentum < 0.0
    if decision == "DOWN":
        return momentum > 0.0
    return False


def _optional_float(value: Any) -> float | None:
    return float(value) if value not in {"", None} else None
