from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

from .active_strategy import DEFAULT_ACTIVE_STRATEGY_STATE
from .canary_readiness import build_canary_readiness_report
from .candidate_change_review import build_candidate_change_review_report
from .candidate_evidence_progress import build_candidate_evidence_progress_report
from .current_strategy_readiness import build_current_strategy_readiness_report
from .snapshot_status import read_snapshot_status


DEFAULT_DASHBOARD_OUTPUT = Path("canary_dashboard.html")
DEFAULT_SNAPSHOT_PATH = Path("data/ws_orderbook_snapshots.csv")
DEFAULT_WINDOW_SUMMARY_PATH = Path("data/ws_orderbook_window_summary.csv")
DEFAULT_SETTLED_WINDOWS_PATH = Path("data/settled_snapshot_windows.csv")
DEFAULT_FORWARD_LEDGER_PATH = Path("data/forward_snapshot_evaluations.csv")

CANARY_WIN_RATE_FLOOR = 0.55
MIN_CANDIDATE_TRADES = 10
MIN_TRADE_RETENTION = 0.50
MIN_CANDIDATE_ELIGIBLE_WINDOWS = 30
MIN_CANDIDATE_DIVERGENT_WINDOWS = 10


@dataclass(frozen=True)
class CsvFileStatus:
    rows: int
    latest: dict[str, str]


def build_canary_dashboard_data(
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
    window_summary_path: Path = DEFAULT_WINDOW_SUMMARY_PATH,
    settled_windows_path: Path = DEFAULT_SETTLED_WINDOWS_PATH,
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER_PATH,
    strategy_state_path: Path = DEFAULT_ACTIVE_STRATEGY_STATE,
) -> dict[str, Any]:
    readiness_report = build_canary_readiness_report(forward_ledger_path=forward_ledger_path)
    change_review = build_candidate_change_review_report(forward_ledger_path=forward_ledger_path)
    progress = build_candidate_evidence_progress_report()
    current_strategy = build_current_strategy_readiness_report(
        forward_ledger_path=forward_ledger_path,
        strategy_state_path=strategy_state_path,
    )
    files = {
        "snapshots": read_csv_file_status(snapshot_path),
        "window_summary": read_csv_file_status(window_summary_path),
        "settled_windows": read_csv_file_status(settled_windows_path),
        "forward_evals": read_csv_file_status(forward_ledger_path),
    }
    snapshot_status = read_snapshot_status(snapshot_path)
    forward = change_review["forward_summary"]
    readiness = readiness_report["readiness"]
    metrics = readiness["metrics"]
    wins_needed = consecutive_wins_needed(
        wins=int(forward["wins"]),
        trades=int(forward["traded_rows"]),
        target=CANARY_WIN_RATE_FLOOR,
    )

    review_by_id = {
        item["candidate_id"]: item for item in change_review["candidate_reviews"]
    }
    active_candidates = []
    for item in progress["items"]:
        if not item["active"]:
            continue
        review = review_by_id.get(item["candidate_id"], {})
        review_metrics = review.get("metrics", {})
        active_candidates.append(
            {
                **item,
                "review_blockers": list(review.get("blockers", ())),
                "review_warnings": list(review.get("warnings", ())),
                "trade_retention": float(review_metrics.get("trade_retention", 0.0)),
                "candidate_total_pnl_usd": float(
                    review_metrics.get("candidate_total_pnl_usd", 0.0)
                ),
                "active_total_pnl_usd": float(review_metrics.get("active_total_pnl_usd", 0.0)),
                "candidate_trades_needed": max(
                    0,
                    MIN_CANDIDATE_TRADES - int(review_metrics.get("candidate_trades", item["candidate_trades"])),
                ),
                "retention_gap": max(
                    0.0,
                    MIN_TRADE_RETENTION - float(review_metrics.get("trade_retention", 0.0)),
                ),
            }
        )

    next_candidate = choose_dashboard_next_candidate(active_candidates)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "readiness": readiness,
        "readiness_metrics": metrics,
        "readiness_blockers": list(readiness["blockers"]),
        "readiness_warnings": list(readiness["warnings"]),
        "change_review": change_review["decision"],
        "forward_summary": forward,
        "forward_wins_needed_for_floor": wins_needed,
        "candidate_progress": progress,
        "active_candidates": active_candidates,
        "next_candidate": next_candidate,
        "current_strategy_readiness": current_strategy["readiness"],
        "current_strategy_state": current_strategy["active_strategy_state"],
        "snapshot_status": snapshot_status,
        "files": {key: value.__dict__ for key, value in files.items()},
        "policy": {
            "canary_win_rate_floor": CANARY_WIN_RATE_FLOOR,
            "min_candidate_trades": MIN_CANDIDATE_TRADES,
            "min_trade_retention": MIN_TRADE_RETENTION,
            "min_candidate_eligible_windows": MIN_CANDIDATE_ELIGIBLE_WINDOWS,
            "min_candidate_divergent_windows": MIN_CANDIDATE_DIVERGENT_WINDOWS,
        },
    }


def read_csv_file_status(path: Path) -> CsvFileStatus:
    if not path.exists():
        return CsvFileStatus(rows=0, latest={})
    with path.open(newline="", encoding="utf-8") as handle:
        rows = 0
        latest: dict[str, str] = {}
        for row in csv.DictReader(handle):
            rows += 1
            latest = row
    return CsvFileStatus(rows=rows, latest=latest)


def consecutive_wins_needed(wins: int, trades: int, target: float) -> int:
    if trades <= 0:
        return 1
    if wins / trades >= target:
        return 0
    added = 0
    while (wins + added) / (trades + added) < target:
        added += 1
    return added


def choose_dashboard_next_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    passed = [item for item in candidates if item["change_quality_passed"]]
    if passed:
        return sorted(passed, key=lambda item: item["delta_pnl_usd"], reverse=True)[0]
    review_ready = [item for item in candidates if item["review_ready"]]
    if review_ready:
        return sorted(review_ready, key=lambda item: item["delta_pnl_usd"], reverse=True)[0]
    estimable = [
        item for item in candidates if item.get("estimated_minutes_to_review") is not None
    ]
    if estimable:
        return sorted(
            estimable,
            key=lambda item: (item["estimated_minutes_to_review"], -item["delta_pnl_usd"]),
        )[0]
    return sorted(candidates, key=lambda item: item["candidate_id"])[0]


def render_canary_dashboard_html(data: dict[str, Any]) -> str:
    readiness = data["readiness"]
    metrics = data["readiness_metrics"]
    forward = data["forward_summary"]
    policy = data["policy"]
    ready = bool(readiness["ready"])
    top_class = "ok" if ready else "blocked"
    top_text = "CANARY READY" if ready else "CANARY BLOCKED"
    live_text = "等待 Lee 明确授权" if ready else "真实下单禁用"
    win_rate = float(metrics["forward_win_rate"])
    win_rate_floor = float(policy["canary_win_rate_floor"])
    win_rate_pct = win_rate * 100
    floor_pct = win_rate_floor * 100
    win_progress = min(100.0, 100.0 * win_rate / win_rate_floor) if win_rate_floor else 0.0
    candidate_quality_passed = metrics.get("quality_passed_candidates", [])

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="refresh" content="60" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>BTC Polymarket Canary Dashboard</title>
  <style>
    :root {{
      --bg: #0b1020;
      --panel: #11182c;
      --panel2: #151f38;
      --text: #ecf2ff;
      --muted: #93a4c4;
      --line: #24304b;
      --good: #36d399;
      --warn: #fbbf24;
      --bad: #fb7185;
      --info: #60a5fa;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--text); font-family: Inter, "Segoe UI", Arial, sans-serif; }}
    main {{ max-width: 1280px; margin: 0 auto; padding: 24px; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    h2 {{ margin: 0 0 14px; font-size: 18px; }}
    .muted {{ color: var(--muted); }}
    .hero {{ display: grid; grid-template-columns: 1.2fr .8fr; gap: 16px; margin-bottom: 16px; }}
    .panel {{ background: linear-gradient(180deg, var(--panel), var(--panel2)); border: 1px solid var(--line); border-radius: 18px; padding: 18px; box-shadow: 0 10px 30px rgba(0,0,0,.24); }}
    .status {{ font-size: 34px; font-weight: 800; letter-spacing: .5px; }}
    .status.ok {{ color: var(--good); }}
    .status.blocked {{ color: var(--bad); }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0; }}
    .metric {{ background: rgba(255,255,255,.035); border: 1px solid var(--line); border-radius: 14px; padding: 14px; }}
    .metric .label {{ color: var(--muted); font-size: 12px; margin-bottom: 8px; }}
    .metric .value {{ font-size: 24px; font-weight: 750; }}
    .metric .sub {{ color: var(--muted); font-size: 12px; margin-top: 6px; }}
    .bar {{ height: 9px; background: #26304a; border-radius: 999px; overflow: hidden; margin-top: 10px; }}
    .fill {{ height: 100%; background: var(--info); border-radius: 999px; }}
    .fill.good {{ background: var(--good); }}
    .fill.warn {{ background: var(--warn); }}
    .fill.bad {{ background: var(--bad); }}
    .pill {{ display: inline-flex; align-items: center; gap: 6px; border-radius: 999px; padding: 5px 10px; font-size: 12px; font-weight: 700; }}
    .pill.good {{ background: rgba(54,211,153,.16); color: var(--good); }}
    .pill.warn {{ background: rgba(251,191,36,.16); color: var(--warn); }}
    .pill.bad {{ background: rgba(251,113,133,.16); color: var(--bad); }}
    .pill.info {{ background: rgba(96,165,250,.16); color: var(--info); }}
    .two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }}
    table {{ width: 100%; border-collapse: collapse; overflow: hidden; border-radius: 12px; }}
    th, td {{ padding: 11px 10px; border-bottom: 1px solid var(--line); text-align: left; font-size: 13px; vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 650; background: rgba(255,255,255,.035); }}
    tr:last-child td {{ border-bottom: none; }}
    .nowrap {{ white-space: nowrap; }}
    .small {{ font-size: 12px; }}
    .blockers {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }}
    .footer {{ margin: 20px 0 4px; color: var(--muted); font-size: 12px; }}
    @media (max-width: 980px) {{ .hero, .two, .grid {{ grid-template-columns: 1fr; }} main {{ padding: 14px; }} }}
  </style>
</head>
<body>
<main>
  <div class="hero">
    <section class="panel">
      <div class="muted">BTC Polymarket 5m Canary Readiness</div>
      <h1>{escape(top_text)}</h1>
      <div class="status {top_class}">{escape(live_text)}</div>
      <div class="blockers">{render_pills(data["readiness_blockers"], "bad")}</div>
      <p class="muted">生成时间 UTC：{escape(data["generated_at"])}。浏览器每 60 秒自动刷新页面，文件由 watchdog 每 5 分钟生成。</p>
    </section>
    <section class="panel">
      <h2>下一步最重要的缺口</h2>
      {render_next_gap(data)}
    </section>
  </div>

  <section class="grid">
    <div class="metric"><div class="label">前向评估</div><div class="value">{int(metrics['forward_evaluations'])}</div><div class="sub">已过评审样本门槛</div></div>
    <div class="metric"><div class="label">纸面交易</div><div class="value">{int(metrics['forward_trades'])}</div><div class="sub">胜 {int(forward['wins'])}，负 {int(forward['losses'])}</div></div>
    <div class="metric"><div class="label">当前胜率</div><div class="value">{win_rate_pct:.1f}%</div><div class="bar"><div class="fill {'good' if win_rate >= win_rate_floor else 'bad'}" style="width:{win_progress:.1f}%"></div></div><div class="sub">目标 {floor_pct:.1f}%，还需连续胜 {int(data['forward_wins_needed_for_floor'])} 笔</div></div>
    <div class="metric"><div class="label">纸面 PnL</div><div class="value">{money(metrics['forward_total_pnl_usd'])}</div><div class="sub">正数不能替代胜率门槛</div></div>
  </section>

  <div class="two">
    <section class="panel">
      <h2>数据采集</h2>
      {render_data_collection(data)}
    </section>
    <section class="panel">
      <h2>Canary 门</h2>
      {render_gate_list(data, candidate_quality_passed)}
    </section>
  </div>

  <section class="panel" style="margin-bottom:16px;">
    <h2>当前纸面策略版本</h2>
    {render_current_strategy(data)}
  </section>

  <section class="panel">
    <h2>候选策略进度</h2>
    {render_candidate_table(data['active_candidates'])}
  </section>

  <div class="footer">边界：这个 dashboard 只展示证据成熟度，不启用真实下单，不读取私钥，不提交订单。</div>
</main>
</body>
</html>
"""


def render_next_gap(data: dict[str, Any]) -> str:
    metrics = data["readiness_metrics"]
    next_candidate = data.get("next_candidate")
    parts = []
    if float(metrics["forward_win_rate"]) < CANARY_WIN_RATE_FLOOR:
        parts.append(
            f"<p><span class='pill bad'>胜率缺口</span> 当前 {pct(metrics['forward_win_rate'])}，目标 {pct(CANARY_WIN_RATE_FLOOR)}。如果后续全胜，至少还要 {int(data['forward_wins_needed_for_floor'])} 笔胜单。</p>"
        )
    if not metrics.get("quality_passed_candidates"):
        if next_candidate:
            parts.append(
                "<p><span class='pill warn'>候选质量缺口</span> "
                f"当前最接近：<b>{escape(next_candidate['candidate_id'])}</b>。"
                f"候选交易还差 {int(next_candidate['candidate_trades_needed'])} 笔，"
                f"交易保留率还差 {pct(next_candidate['retention_gap'])}。</p>"
            )
        else:
            parts.append("<p><span class='pill warn'>候选质量缺口</span> 尚无活跃候选。</p>")
    if not parts:
        parts.append("<p><span class='pill good'>主要门槛已过</span> 等待 Lee 手动授权 canary 包。</p>")
    return "".join(parts)


def render_data_collection(data: dict[str, Any]) -> str:
    files = data["files"]
    snapshot = data["snapshot_status"]
    rows = [
        ("盘口快照", files["snapshots"]["rows"], snapshot.get("latest_captured_at", "")),
        ("盘口窗口", files["window_summary"]["rows"], files["window_summary"]["latest"].get("slug", "")),
        ("已结算窗口", files["settled_windows"]["rows"], files["settled_windows"]["latest"].get("slug", "")),
        ("前向评估", files["forward_evals"]["rows"], files["forward_evals"]["latest"].get("slug", "")),
    ]
    body = "".join(
        f"<tr><td>{escape(name)}</td><td class='nowrap'>{count}</td><td class='small muted'>{escape(str(latest))}</td></tr>"
        for name, count, latest in rows
    )
    return f"<table><thead><tr><th>项目</th><th>数量</th><th>最新</th></tr></thead><tbody>{body}</tbody></table>"


def render_gate_list(data: dict[str, Any], candidate_quality_passed: list[str]) -> str:
    metrics = data["readiness_metrics"]
    current_strategy = data["current_strategy_readiness"]
    gates = [
        ("前向评估 100+", int(metrics["forward_evaluations"]) >= 100, str(metrics["forward_evaluations"])),
        ("纸面交易 30+", int(metrics["forward_trades"]) >= 30, str(metrics["forward_trades"])),
        ("胜率 55%+", float(metrics["forward_win_rate"]) >= CANARY_WIN_RATE_FLOOR, pct(metrics["forward_win_rate"])),
        ("当前策略版本", bool(current_strategy["ready"]), "ready" if current_strategy["ready"] else "collecting"),
        ("候选 review ready", bool(metrics.get("review_ready_candidates")), ", ".join(metrics.get("review_ready_candidates", [])) or "无"),
        ("候选质量通过", bool(candidate_quality_passed), ", ".join(candidate_quality_passed) or "无"),
        ("Mock 提交已见", int(metrics.get("accepted_attempts", 0)) > 0, str(metrics.get("accepted_attempts", 0))),
    ]
    body = "".join(
        f"<tr><td>{escape(name)}</td><td>{render_status(ok)}</td><td>{escape(value)}</td></tr>"
        for name, ok, value in gates
    )
    return f"<table><thead><tr><th>门槛</th><th>状态</th><th>当前</th></tr></thead><tbody>{body}</tbody></table>"


def render_current_strategy(data: dict[str, Any]) -> str:
    readiness = data["current_strategy_readiness"]
    metrics = readiness["metrics"]
    state = data["current_strategy_state"]
    rows = [
        ("source", state["source_candidate_id"]),
        ("filter", state["filter_kind"]),
        ("activated_at", state["activated_at"]),
        ("evaluations", str(metrics["current_strategy_evaluations"])),
        ("trades", str(metrics["current_strategy_trades"])),
        ("win_rate", pct(metrics["current_strategy_win_rate"])),
        ("total_pnl", money(metrics["current_strategy_total_pnl_usd"])),
        ("blockers", ", ".join(readiness["blockers"]) or "无"),
    ]
    body = "".join(
        f"<tr><td>{escape(name)}</td><td>{escape(value)}</td></tr>"
        for name, value in rows
    )
    return f"<table><tbody>{body}</tbody></table>"


def render_candidate_table(candidates: list[dict[str, Any]]) -> str:
    if not candidates:
        return "<p class='muted'>暂无活跃候选。</p>"
    rows = []
    for item in candidates:
        eta = item.get("estimated_minutes_to_review")
        rows.append(
            "<tr>"
            f"<td><b>{escape(item['candidate_id'])}</b><div class='small muted'>{escape(item['blocker_kind'])}</div></td>"
            f"<td>{render_status(bool(item['review_ready']))}</td>"
            f"<td>{render_status(bool(item['change_quality_passed']))}</td>"
            f"<td>{int(item['eligible_windows'])}/{MIN_CANDIDATE_ELIGIBLE_WINDOWS}<div class='bar'><div class='fill info' style='width:{progress_width(item['eligible_windows'], MIN_CANDIDATE_ELIGIBLE_WINDOWS):.1f}%'></div></div></td>"
            f"<td>{int(item['divergent_windows'])}/{MIN_CANDIDATE_DIVERGENT_WINDOWS}<div class='bar'><div class='fill info' style='width:{progress_width(item['divergent_windows'], MIN_CANDIDATE_DIVERGENT_WINDOWS):.1f}%'></div></div></td>"
            f"<td>{int(item['candidate_trades'])}/{MIN_CANDIDATE_TRADES}</td>"
            f"<td>{pct(item['trade_retention'])}</td>"
            f"<td>{money(item['delta_pnl_usd'])}</td>"
            f"<td>{pct(item['candidate_win_rate'])}</td>"
            f"<td>{'已到' if eta == 0 else (str(eta) + ' 分钟' if eta is not None else '未知')}</td>"
            f"<td class='small'>{escape(', '.join(item['review_blockers']) or '无')}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr>"
        "<th>候选</th><th>Review</th><th>质量</th><th>Eligible</th><th>Divergent</th>"
        "<th>候选交易</th><th>保留率</th><th>Delta</th><th>胜率</th><th>ETA</th><th>阻塞</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def render_pills(items: list[str], kind: str) -> str:
    if not items:
        return "<span class='pill good'>none</span>"
    return "".join(f"<span class='pill {kind}'>{escape(item)}</span>" for item in items)


def render_status(ok: bool) -> str:
    return "<span class='pill good'>PASS</span>" if ok else "<span class='pill bad'>BLOCK</span>"


def progress_width(value: float, target: float) -> float:
    if target <= 0:
        return 100.0
    return max(0.0, min(100.0, 100.0 * float(value) / target))


def pct(value: float) -> str:
    return f"{float(value) * 100:.1f}%"


def money(value: float) -> str:
    return f"{float(value):+.2f} USDC"


def write_canary_dashboard(
    output_path: Path = DEFAULT_DASHBOARD_OUTPUT,
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
    window_summary_path: Path = DEFAULT_WINDOW_SUMMARY_PATH,
    settled_windows_path: Path = DEFAULT_SETTLED_WINDOWS_PATH,
    forward_ledger_path: Path = DEFAULT_FORWARD_LEDGER_PATH,
    strategy_state_path: Path = DEFAULT_ACTIVE_STRATEGY_STATE,
) -> dict[str, Any]:
    data = build_canary_dashboard_data(
        snapshot_path=snapshot_path,
        window_summary_path=window_summary_path,
        settled_windows_path=settled_windows_path,
        forward_ledger_path=forward_ledger_path,
        strategy_state_path=strategy_state_path,
    )
    output_path.write_text(render_canary_dashboard_html(data), encoding="utf-8")
    return data
