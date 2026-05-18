# 候选策略证据成熟度报告

## 目标

区分“看过多少未来窗口”和“这些窗口到底有没有给候选提供信息”。

## 核心指标

- `eligible_windows`
- `divergent_windows`
- `candidate_filter_windows`
- `active_trades`
- `candidate_trades`
- `delta_pnl_usd`

## 复盘门槛

- 至少 `30` 个未来窗口
- 至少 `10` 个候选与激活策略产生不同决策的窗口

如果窗口很多但决策从不分叉，候选就还没有真正接受检验。

## 当前状态

- `edge_008`
  - `eligible_windows = 4`
  - `divergent_windows = 0`
- `avoid_low_momentum_near_barrier`
  - `eligible_windows = 1`
  - `divergent_windows = 0`

两者都仍处于 `collecting`。当前最缺的不是更多候选，而是足够多真正会让候选和激活策略分道扬镳的未来窗口。
